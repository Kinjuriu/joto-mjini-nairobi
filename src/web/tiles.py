"""v2 web tiles: static XYZ folders for Mapbox GL JS, plus site/public/tiles/manifest.json.

Raster layers become WebP tiles (`site/public/tiles/<layer>/{z}/{x}/{y}.webp`) with the colour ramps of
prompts/v2/DESIGN_BRIEF_v2.md baked in and transparent outside the county or where there is no data.
Values (not colours) are resampled into each Web Mercator tile: area-average when the tile pixel is
larger than the source pixel, bilinear when it is smaller, so classed colours get smooth edges instead
of square 30 m or 100 m blocks. Categorical land cover uses mode and nearest neighbour.

Vector layers become uncompressed .pbf folders from tippecanoe (`--output-to-directory`).

Run: uv run python -m src.web.tiles [--only heat-diff,landcover,...] [--force]
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Callable

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from PIL import Image
from rasterio.features import rasterize
from rasterio.transform import Affine
from rasterio.warp import Resampling, reproject

from src.config import BOUNDARY, INTERIM, PROCESSED, RASTERS, ROOT, UTM, WEB, WGS84, get_logger

log = get_logger("web_tiles")

TILES = ROOT / "site" / "public" / "tiles"
TABLES = ROOT / "analysis" / "tables"
RESULTS = ROOT / "analysis" / "results.json"
R = 6378137.0
ORIGIN = math.pi * R
TILE = 256

# ------------------------------------------------------------------ colour ramps (design brief v2)
DIFF_BREAKS = [-6, -4, -2, -0.5, 0.5, 2, 4, 6]
DIFF_COLOURS = ["#1D4E6F", "#3B7CA6", "#8DBAD6", "#C9DDE9", "#F2EFE9", "#F6CBA6", "#F4A26B", "#D9542B", "#A1201A"]
DIFF_LABELS = ["−6 or cooler", "−6 to −4", "−4 to −2", "−2 to −0.5", "about the same", "+0.5 to +2", "+2 to +4",
               "+4 to +6", "+6 or hotter"]
YLORBR = ["#FFF7D6", "#FEE391", "#FEC44F", "#FB9A29", "#EC7014", "#CC4C02", "#8C2D04"]
GREENS = ["#D9EBC7", "#9CC98A", "#5A9E5C", "#2E6B3F"]
PURPLES = ["#F2F0F7", "#CBC9E2", "#9E9AC8", "#756BB1", "#54278F"]
WC = {10: ("Tree cover", "#2E6B3F"), 20: ("Shrubland", "#8FB573"), 30: ("Grassland", "#E3D9A0"),
      40: ("Cropland", "#D8A657"), 50: ("Built-up", "#C8423A"), 60: ("Bare or sparse", "#B9B0A2"),
      80: ("Water", "#3E6FA8"), 90: ("Wetland", "#6FA9A8")}
GROWTH_OLD, GROWTH_NEW = "#6B6B6B", "#C8423A"
GHSL_COLOURS = ["#EBC2B2", "#D77A62", "#B5362B"]
GHSL_BREAKS = [0.10, 0.30, 0.60]           # share of the cell built-up; under 10 % transparent
BUILT_THRESHOLD = 0.25                     # growth map: a cell counts as built-up from 25 % built surface
TREE_BREAKS = [0.10, 0.25, 0.50, 0.75]     # under 10 % transparent

LST_SOURCE = "Landsat 8 and 9 Collection 2 Level-2 (USGS) via Microsoft Planetary Computer; analysis: Joto Mjini Nairobi"
S2_SOURCE = "Contains modified Copernicus Sentinel data 2026, processed by Joto Mjini Nairobi"


def _rgb(h: str) -> tuple[int, int, int]:
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def classify(v: np.ndarray, breaks: list[float], colours: list[str], valid: np.ndarray) -> np.ndarray:
    """RGBA for classes: len(colours) == len(breaks) + 1; values beyond either end take the end colour."""
    idx = np.digitize(v, breaks)
    lut = np.array([(*_rgb(c), 255) for c in colours], dtype="uint8")
    out = lut[np.clip(idx, 0, len(colours) - 1)]
    out[~valid] = 0
    return out


def classify_from(v: np.ndarray, breaks: list[float], colours: list[str], valid: np.ndarray) -> np.ndarray:
    """Like classify, but values under breaks[0] are transparent; len(colours) == len(breaks)."""
    idx = np.digitize(v, breaks) - 1
    lut = np.array([(*_rgb(c), 255) for c in colours], dtype="uint8")
    out = lut[np.clip(idx, 0, len(colours) - 1)]
    out[~valid | (idx < 0)] = 0
    return out


# ------------------------------------------------------------------ tile maths
def lonlat_to_m(lon: float, lat: float) -> tuple[float, float]:
    x = math.radians(lon) * R
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * R
    return x, y


def tile_range(bounds: tuple[float, float, float, float], z: int) -> tuple[int, int, int, int]:
    """xmin, ymin, xmax, ymax tile indices (inclusive) covering lon/lat bounds."""
    w, s, e, n = bounds
    n_t = 2 ** z

    def tx(lon):
        return int((lon + 180) / 360 * n_t)

    def ty(lat):
        lr = math.radians(lat)
        return int((1 - math.log(math.tan(lr) + 1 / math.cos(lr)) / math.pi) / 2 * n_t)
    return tx(w), ty(n), tx(e), ty(s)


def tile_transform(z: int, x: int, y: int) -> Affine:
    size = 2 * ORIGIN / 2 ** z
    return Affine(size / TILE, 0, -ORIGIN + x * size, 0, -size / TILE, ORIGIN - y * size)


# ------------------------------------------------------------------ layer definitions
@dataclass
class Source:
    path: Path
    band: int | list[int] = 1
    categorical: bool = False
    nodata: float | None = None


@dataclass
class RasterLayer:
    id: str
    title: str
    sources: list[Source]
    colourise: Callable[[list[np.ndarray], np.ndarray], np.ndarray]   # (resampled arrays, valid mask) -> RGBA
    minzoom: int = 9
    maxzoom: int = 15
    mask_county: bool = True
    lossless: bool = False
    legend: dict = field(default_factory=dict)
    description: str = ""
    source_line: str = ""
    chip: str = ""
    resampling: str = "linear"     # what the map should use when overzooming


def _county_3857() -> gpd.GeoDataFrame:
    return gpd.read_file(BOUNDARY).to_crs(WEB)


def render(layer: RasterLayer, force: bool = False) -> dict:
    out_dir = TILES / layer.id
    if out_dir.exists() and not force:
        log.info("%s: exists, skipping (use --force)", layer.id)
        return _stats(out_dir)
    if out_dir.exists():
        trash = ROOT / "_trash" / "tiles"
        trash.mkdir(parents=True, exist_ok=True)
        shutil.move(str(out_dir), str(trash / f"{layer.id}_{pd.Timestamp.now():%Y%m%d%H%M%S}"))
    county = _county_3857()
    cgeom = county.union_all()
    srcs = [rasterio.open(s.path) for s in layer.sources]
    if layer.mask_county:
        b = gpd.GeoSeries([cgeom], crs=WEB).to_crs(WGS84).total_bounds
    else:
        b = gpd.GeoSeries.from_xy([srcs[0].bounds.left, srcs[0].bounds.right], [srcs[0].bounds.bottom, srcs[0].bounds.top],
                                  crs=srcs[0].crs).to_crs(WGS84).total_bounds
        bc = gpd.GeoSeries([cgeom], crs=WEB).to_crs(WGS84).total_bounds
        b = [max(b[0], bc[0] - 0.03), max(b[1], bc[1] - 0.03), min(b[2], bc[2] + 0.03), min(b[3], bc[3] + 0.03)]
    bounds = tuple(float(v) for v in b)
    data = []
    for s, src in zip(layer.sources, srcs):
        bands = s.band if isinstance(s.band, list) else [s.band]
        arr = src.read(bands).astype("float32")
        nd = s.nodata if s.nodata is not None else src.nodata
        if nd is not None and not (isinstance(nd, float) and math.isnan(nd)):
            arr[arr == nd] = np.nan
        data.append((arr, src.transform, src.crs, s))
    n_tiles = 0
    for z in range(layer.minzoom, layer.maxzoom + 1):
        x0, y0, x1, y1 = tile_range(bounds, z)
        width = (x1 - x0 + 1) * TILE
        for ty in range(y0, y1 + 1):
            st = tile_transform(z, x0, ty)
            dst_res = st.a
            arrays = []
            for arr, t, crs, s in data:
                src_res = abs(t.a) if crs.is_projected else abs(t.a) * 111320
                if s.categorical:
                    rs = Resampling.mode if dst_res > src_res * 1.2 else Resampling.nearest
                else:
                    rs = Resampling.average if dst_res > src_res * 1.2 else Resampling.bilinear
                out = np.full((arr.shape[0], TILE, width), np.nan, dtype="float32")
                reproject(arr, out, src_transform=t, src_crs=crs, dst_transform=st, dst_crs=WEB,
                          resampling=rs, src_nodata=np.nan, dst_nodata=np.nan)
                arrays.append(out if arr.shape[0] > 1 else out[0])
            valid = np.isfinite(arrays[0]) if arrays[0].ndim == 2 else np.isfinite(arrays[0]).all(0)
            if layer.mask_county:
                cm = rasterize([(cgeom, 1)], out_shape=(TILE, width), transform=st, fill=0, dtype="uint8") == 1
                valid &= cm
            rgba = layer.colourise(arrays, valid)
            for i, tx in enumerate(range(x0, x1 + 1)):
                tile = rgba[:, i * TILE:(i + 1) * TILE]
                p = out_dir / str(z) / str(tx) / f"{ty}.webp"
                p.parent.mkdir(parents=True, exist_ok=True)
                buf = BytesIO()
                Image.fromarray(tile, "RGBA").save(buf, format="WEBP", lossless=layer.lossless,
                                                   quality=100 if layer.lossless else 82, method=4)
                p.write_bytes(buf.getvalue())
                n_tiles += 1
        log.info("%s z%d: tiles x %d-%d, y %d-%d", layer.id, z, x0, x1, y0, y1)
    for s in srcs:
        s.close()
    st = _stats(out_dir)
    st["bounds"] = [round(v, 5) for v in bounds]
    (out_dir / "_bounds.json").write_text(json.dumps(st["bounds"]))
    log.info("%s: %d tiles, %.1f MB", layer.id, n_tiles, st["size_mb"])
    return st


def _stats(d: Path) -> dict:
    files = [p for p in d.rglob("*") if p.is_file()]
    st = dict(n_tiles=sum(1 for p in files if p.suffix in (".webp", ".pbf")),
              size_mb=round(sum(p.stat().st_size for p in files) / 1e6, 1),
              largest_kb=round(max((p.stat().st_size for p in files), default=0) / 1e3, 1))
    bj = d / "_bounds.json"
    if bj.exists():
        st["bounds"] = json.loads(bj.read_text())
    return st


# ------------------------------------------------------------------ the layers
def _results() -> dict:
    return json.loads(RESULTS.read_text())


def _county_values(path: Path) -> np.ndarray:
    from src.rasterio_utils import county_mask, read
    a = read(path)
    m = county_mask() & np.isfinite(a)
    return a[m]


def diff_legend(median: float, what: str) -> dict:
    return dict(type="classes", unit="°C difference from the city median",
                note=f"City median {median:.1f} °C ({what})",
                classes=[dict(color=c, label=l) for c, l in zip(DIFF_COLOURS, DIFF_LABELS)])


def build_layers() -> list[RasterLayer]:
    res = _results()
    med_hot = res["q1"]["county_median_c"]
    hcd = res["composites"]["hottest_clear_day"]
    med_day = float(np.median(_county_values(RASTERS / "lst_hottest_clear_day.tif")))
    med_cool = float(np.median(_county_values(RASTERS / "lst_cool_season_median.tif")))
    hot_vals = _county_values(RASTERS / "lst_hot_season_median.tif")
    abs_breaks = [round(float(v), 1) for v in np.percentile(hot_vals, [10, 20, 40, 60, 80, 90])]
    # Population density (people per km2) from the native 100 m WorldPop grid; quantile breaks of
    # populated cells inside the county.
    pop_path = RASTERS / "population_100m.tif"
    with rasterio.open(pop_path) as s:
        pa = s.read(1)
        lat = s.bounds.bottom + (np.arange(s.height)[::-1] + 0.5) * abs(s.transform.e)
        cell_km2 = (abs(s.transform.a) * 111.32 * np.cos(np.radians(lat))[:, None]) * (abs(s.transform.e) * 110.57)
        dens = pa / cell_km2
        prof = s.profile
    dens_path = INTERIM / "population_density_100m.tif"
    prof.update(dtype="float32", nodata=np.nan)
    with rasterio.open(dens_path, "w", **prof) as d:
        d.write(dens.astype("float32"), 1)
    cm = rasterize([(gpd.read_file(BOUNDARY).to_crs(prof["crs"]).union_all(), 1)], out_shape=pa.shape,
                   transform=prof["transform"], fill=0) == 1
    pv = dens[cm & np.isfinite(dens) & (dens > 0)]
    pop_breaks = [0.0] + [float(round(v, -2)) for v in np.percentile(pv, [20, 40, 60, 80])]
    pop_floor = 100.0   # people per km2; lighter than that stays transparent so the basemap shows through

    def diff(median):
        return lambda a, v: classify(a[0] - median, DIFF_BREAKS, DIFF_COLOURS, v)

    def wc(a, v):
        out = np.zeros(a[0].shape + (4,), dtype="uint8")
        for k, (_, c) in WC.items():
            m = v & (np.rint(a[0]) == k)
            out[m] = (*_rgb(c), 255)
        return out

    def growth(a, v):
        old = a[0] >= BUILT_THRESHOLD
        new = (a[1] >= BUILT_THRESHOLD) & ~old
        out = np.zeros(a[0].shape + (4,), dtype="uint8")
        out[v & old] = (*_rgb(GROWTH_OLD), 255)
        out[v & new] = (*_rgb(GROWTH_NEW), 255)
        return out

    def rgb_img(a, v):
        rgb = np.nan_to_num(a[0], nan=0).clip(0, 255).astype("uint8")
        alpha = (v & (rgb.sum(0) > 0)).astype("uint8") * 255
        return np.dstack([rgb[0], rgb[1], rgb[2], alpha])

    hot = Source(RASTERS / "lst_hot_season_median.tif")
    pop_labels = [f"{int(pop_breaks[i]):,} to {int(pop_breaks[i + 1]):,}" for i in range(1, 4)]
    layers = [
        RasterLayer("heat-diff", "Surface temperature: difference from the city median", [hot], diff(med_hot),
                    legend=diff_legend(med_hot, "January to March mornings, 2023 to 2026"),
                    description=f"How much hotter or cooler the ground was than the county median ({med_hot:.1f} °C) on "
                                "clear January to March mornings, 2023 to 2026. Land surface temperature measured by "
                                "Landsat at about 100 m; it is the heat of the ground, roofs and roads, not of the air.",
                    source_line=LST_SOURCE, chip="January to March mornings, 2023 to 2026"),
        RasterLayer("heat-abs", "Land surface temperature", [hot],
                    lambda a, v: classify(a[0], abs_breaks, YLORBR, v),
                    legend=dict(type="classes", unit="°C", note="Breaks at the county's deciles",
                                classes=[dict(color=c, label=l) for c, l in zip(
                                    YLORBR, [f"under {abs_breaks[0]:.1f}"] +
                                    [f"{abs_breaks[i]:.1f} to {abs_breaks[i + 1]:.1f}" for i in range(5)] +
                                    [f"{abs_breaks[5]:.1f} or more"])]),
                    description="Median land surface temperature on clear January to March mornings, 2023 to 2026, "
                                "from 12 Landsat 8 and 9 scenes. Colour breaks sit at the county's deciles, so each "
                                "colour covers a similar share of the city.",
                    source_line=LST_SOURCE, chip="January to March mornings, 2023 to 2026"),
        RasterLayer("heat-cool-abs", "Land surface temperature, cool season (hot-season scale)",
                    [Source(RASTERS / "lst_cool_season_median.tif")],
                    lambda a, v: classify(a[0], abs_breaks, YLORBR, v),
                    legend=dict(type="classes", unit="°C", note="Same colours as the hot-season map",
                                classes=[dict(color=c, label=l) for c, l in zip(
                                    YLORBR, [f"under {abs_breaks[0]:.1f}"] +
                                    [f"{abs_breaks[i]:.1f} to {abs_breaks[i + 1]:.1f}" for i in range(5)] +
                                    [f"{abs_breaks[5]:.1f} or more"])]),
                    description="Median land surface temperature on clear June to August mornings (4 Landsat scenes, "
                                "2018 to 2026), coloured with the same breaks as the January to March map so the two "
                                "can be compared directly.",
                    source_line=LST_SOURCE, chip="June to August mornings, 2018 to 2026"),
        RasterLayer("heat-hottest-day", "Hottest clear morning: difference from that day's median",
                    [Source(RASTERS / "lst_hottest_clear_day.tif")], diff(med_day),
                    legend=diff_legend(med_day, f"{hcd['date']}"),
                    description=f"Land surface temperature on the hottest clear morning in the record "
                                f"({hcd['date']}), as a difference from that morning's county median ({med_day:.1f} °C).",
                    source_line=LST_SOURCE, chip="29 September 2022, 10:43"),
        RasterLayer("heat-cool-season", "Cool season: difference from its median",
                    [Source(RASTERS / "lst_cool_season_median.tif")], diff(med_cool),
                    legend=diff_legend(med_cool, "June to August mornings"),
                    description=f"Median land surface temperature on clear June to August mornings (4 scenes, 2018 to "
                                f"2026), as a difference from its own county median ({med_cool:.1f} °C).",
                    source_line=LST_SOURCE, chip="June to August mornings, 2018 to 2026"),
        RasterLayer("landcover", "Land cover", [Source(RASTERS / "worldcover_2021.tif", categorical=True, nodata=0)],
                    wc, lossless=True, resampling="nearest",
                    legend=dict(type="categorical", unit="", classes=[dict(color=c, label=n) for n, c in WC.values()]),
                    description="What covers the ground at 10 m, from the European Space Agency's WorldCover map for "
                                "2021.",
                    source_line="ESA WorldCover 10 m 2021 v200 (CC BY 4.0)", chip="2021"),
        RasterLayer("trees", "Tree cover", [Source(RASTERS / "tree_fraction_30m.tif")],
                    lambda a, v: classify_from(a[0], TREE_BREAKS, GREENS, v),
                    legend=dict(type="classes", unit="% of the ground", note="Under 10 % not coloured",
                                classes=[dict(color=c, label=l) for c, l in
                                         zip(GREENS, ["10 to 25 %", "25 to 50 %", "50 to 75 %", "75 % or more"])]),
                    description="Share of each 30 m cell covered by trees, from ESA WorldCover 2021 (10 m).",
                    source_line="ESA WorldCover 10 m 2021 v200 (CC BY 4.0); analysis: Joto Mjini Nairobi", chip="2021"),
        RasterLayer("population", "Where people live", [Source(dens_path)],
                    lambda a, v: classify_from(a[0], [pop_floor] + pop_breaks[1:], PURPLES, v),
                    legend=dict(type="classes", unit="people per km²", note="Breaks at fifths of populated cells",
                                classes=[dict(color=PURPLES[0], label=f"under {int(pop_breaks[1]):,}")] +
                                [dict(color=c, label=l) for c, l in zip(PURPLES[1:4], pop_labels)] +
                                [dict(color=PURPLES[4], label=f"{int(pop_breaks[4]):,} or more")]),
                    description="Estimated people per square kilometre in 2025, from WorldPop's constrained 100 m "
                                "model. A modelled estimate that may undercount the densest settlements.",
                    source_line="WorldPop 2025, constrained, R2025A (CC BY 4.0)", chip="2025 estimate"),
        RasterLayer("growth-1990-2020", "Built-up land, 1990 and 2020",
                    [Source(RASTERS / "ghsl_built_1990.tif"), Source(RASTERS / "ghsl_built_2020.tif")], growth,
                    legend=dict(type="categorical", unit="", note="A cell counts as built-up from 25 % built surface",
                                classes=[dict(color=GROWTH_OLD, label="Built-up by 1990"),
                                         dict(color=GROWTH_NEW, label="Built-up between 1990 and 2020")]),
                    description="Where the city was already built up in 1990 (grey) and where it became built up by "
                                "2020 (red), from the Global Human Settlement Layer's built-up surface.",
                    source_line="GHSL GHS-BUILT-S R2023A, European Commission JRC (CC BY 4.0)", chip="1990 to 2020"),
    ]
    for yr in (1975, 1990, 2000, 2010, 2020, 2025):
        layers.append(RasterLayer(
            f"ghsl-{yr}", f"Built-up surface, {yr}", [Source(RASTERS / f"ghsl_built_{yr}.tif")],
            lambda a, v: classify_from(a[0], GHSL_BREAKS, GHSL_COLOURS, v), maxzoom=14,
            legend=dict(type="classes", unit="% of the ground built up", note="Under 10 % not coloured",
                        classes=[dict(color=c, label=l) for c, l in zip(GHSL_COLOURS, ["10 to 30 %", "30 to 60 %", "60 % or more"])]),
            description=f"Share of the ground covered by buildings in {yr}, from the Global Human Settlement Layer"
                        + (" (2025 is a JRC projection, not an observation)." if yr == 2025 else "."),
            source_line="GHSL GHS-BUILT-S R2023A, European Commission JRC (CC BY 4.0)",
            chip=f"{yr}" + (" (projection)" if yr == 2025 else "")))
    s2 = RASTERS / "s2_true_rgb.tif"
    if s2.exists():
        for name, title, desc in (
                ("true", "Sentinel-2 true colour", "Nairobi as the eye would see it from space: a cloud-free median of "
                                                  "Sentinel-2 images from January to March 2026, at 10 m."),
                ("false", "Sentinel-2 false colour (vegetation in green)",
                 "The same images shown with shortwave infrared, near infrared and red light (bands 12, 8A and 4). "
                 "Living vegetation shows bright green; roofs, roads and bare ground show purple-grey and pink.")):
            layers.append(RasterLayer(
                f"s2-{name}", title, [Source(RASTERS / f"s2_{name}_rgb.tif", band=[1, 2, 3], nodata=0)], rgb_img,
                minzoom=9, maxzoom=16, mask_county=False,
                legend=dict(type="imagery", unit="", classes=[]), description=desc, source_line=S2_SOURCE,
                chip="Sentinel-2, January to March 2026"))
    return layers


# ------------------------------------------------------------------ vector layers
def vectors(force: bool = False) -> dict:
    out = {}
    wards = gpd.read_file(ROOT / "site" / "public" / "data" / "wards.geojson")
    with tempfile.TemporaryDirectory(dir=INTERIM) as td:
        td = Path(td)
        wards.to_file(td / "wards.geojson", driver="GeoJSON")
        # Label points: pole of inaccessibility, so the name sits well inside each ward.
        from shapely.ops import polylabel
        wu = wards.to_crs(UTM)
        pts = [polylabel(g if g.geom_type == "Polygon" else max(g.geoms, key=lambda p: p.area), tolerance=10)
               for g in wu.geometry]
        lab = gpd.GeoDataFrame(wards.drop(columns="geometry"), geometry=pts, crs=UTM).to_crs(WGS84)
        lab["area_km2"] = wu.area / 1e6
        lab[["ward_id", "ward_name", "area_km2", "lst_anomaly_c", "geometry"]].to_file(td / "ward-labels.geojson", driver="GeoJSON")
        places = gpd.read_file(ROOT / "site" / "public" / "data" / "places.geojson")
        places.to_file(td / "places.geojson", driver="GeoJSON")
        b = gpd.read_parquet(PROCESSED / "buildings_lst.parquet")
        b = b[np.isfinite(b["lst_c"])].rename(columns={"lst_anomaly_c": "diff_c"})
        b[["lst_c", "diff_c", "ward_id", "geometry"]].to_file(td / "buildings.geojsonseq", driver="GeoJSONSeq")
        jobs = {
            "wards": (["-l", "wards", "-Z8", "-z14", "--no-simplification-of-shared-nodes", "--detect-shared-borders"], "wards.geojson"),
            "ward-labels": (["-l", "ward-labels", "-Z8", "-z14", "-r1", "--no-feature-limit", "--no-tile-size-limit"], "ward-labels.geojson"),
            "places": (["-l", "places", "-Z8", "-z14", "-r1", "--no-feature-limit"], "places.geojson"),
            "buildings": (["-l", "buildings", "-Z13", "-z16", "--drop-smallest-as-needed", "--simplification=2",
                           "-y", "lst_c", "-y", "diff_c", "-y", "ward_id"], "buildings.geojsonseq"),
        }
        for name, (args, src) in jobs.items():
            d = TILES / name
            if d.exists() and not force:
                out[name] = _stats(d)
                continue
            if d.exists():
                trash = ROOT / "_trash" / "tiles"
                trash.mkdir(parents=True, exist_ok=True)
                shutil.move(str(d), str(trash / f"{name}_{pd.Timestamp.now():%Y%m%d%H%M%S}"))
            cmd = ["tippecanoe", "--output-to-directory", str(d), "--no-tile-compression", "--force", "-q", "-P",
                   *args, str(td / src)]
            subprocess.run(cmd, check=True)
            _fill_empty(d, county_bounds())
            out[name] = _stats(d)
            out[name]["bounds"] = [round(v, 5) for v in county_bounds()]
            (d / "_bounds.json").write_text(json.dumps(out[name]["bounds"]))
            log.info("vector %s: %s", name, out[name])
    return out


def county_bounds() -> tuple[float, float, float, float]:
    b = gpd.read_file(BOUNDARY).to_crs(WGS84).total_bounds
    return (float(b[0]) - 0.01, float(b[1]) - 0.01, float(b[2]) + 0.01, float(b[3]) + 0.01)


def _fill_empty(d: Path, bounds) -> None:
    """tippecanoe skips empty tiles; a zero-byte .pbf is a valid empty vector tile, so no request 404s."""
    meta = json.loads((d / "metadata.json").read_text())
    z0, z1 = int(meta["minzoom"]), int(meta["maxzoom"])
    n = 0
    for z in range(z0, z1 + 1):
        x0, y0, x1, y1 = tile_range(bounds, z)
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                p = d / str(z) / str(x) / f"{y}.pbf"
                if not p.exists():
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(b"")
                    n += 1
    log.info("%s: %d empty tiles written", d.name, n)


# ------------------------------------------------------------------ manifest
VECTOR_META = {
    "wards": dict(title="Wards", description="Nairobi's 85 county assembly wards (IEBC boundaries, via the American "
                                              "Red Cross on HDX), with each ward's numbers.",
                  source_line="Wards: IEBC via American Red Cross, HDX (CC BY)"),
    "ward-labels": dict(title="Ward names", description="", source_line="Wards: IEBC via American Red Cross, HDX (CC BY)"),
    "places": dict(title="Parks, forests and places", description="", source_line="© OpenStreetMap contributors"),
    "buildings": dict(title="Buildings by surface temperature",
                      description="Each building footprint coloured by how much hotter or cooler its surroundings were "
                                  "than the city median on hot mornings. The value describes the area of about 100 m "
                                  "around the building, not the roof itself.",
                      source_line="Buildings: Overture Maps Foundation (ODbL and CDLA); " + LST_SOURCE,
                      chip="January to March mornings, 2023 to 2026"),
}


def manifest(raster_stats: dict, vector_stats: dict) -> None:
    path = TILES / "manifest.json"
    old = json.loads(path.read_text()) if path.exists() else {"layers": {}}
    layers = old.get("layers", {})
    defs = {l.id: l for l in build_layers()}
    for lid, st in raster_stats.items():
        l = defs[lid]
        layers[lid] = dict(id=lid, kind="raster", title=l.title, tiles=f"tiles/{lid}/{{z}}/{{x}}/{{y}}.webp",
                           minzoom=l.minzoom, maxzoom=l.maxzoom, bounds=st.get("bounds"), resampling=l.resampling,
                           legend=l.legend, description=l.description, source=l.source_line, chip=l.chip,
                           n_tiles=st["n_tiles"], size_mb=st["size_mb"])
        if lid == "heat-diff":
            layers[lid]["median_c"] = _results()["q1"]["county_median_c"]
    for lid, st in vector_stats.items():
        m = VECTOR_META[lid]
        layers[lid] = dict(id=lid, kind="vector", source_layer=lid, title=m["title"], bounds=st.get("bounds"),
                           tiles=f"tiles/{lid}/{{z}}/{{x}}/{{y}}.pbf",
                           minzoom={"buildings": 13}.get(lid, 8), maxzoom={"buildings": 16}.get(lid, 14),
                           description=m["description"], source=m["source_line"], chip=m.get("chip", ""),
                           legend=diff_legend(_results()["q1"]["county_median_c"], "January to March mornings, 2023 to 2026")
                           if lid == "buildings" else {}, n_tiles=st["n_tiles"], size_mb=st["size_mb"])
    total = round(sum(v.get("size_mb", 0) for v in layers.values()), 1)
    path.write_text(json.dumps(dict(generated=pd.Timestamp.now(tz="Africa/Nairobi").strftime("%Y-%m-%d %H:%M"),
                                    total_size_mb=total, layers=layers), indent=1, ensure_ascii=False))
    log.info("manifest.json: %d layers, %.1f MB", len(layers), total)


def main(only: list[str] | None = None, force: bool = False) -> None:
    TILES.mkdir(parents=True, exist_ok=True)
    rstats = {}
    for l in build_layers():
        if only and l.id not in only:
            continue
        try:
            rstats[l.id] = render(l, force)
        except Exception as e:   # fail soft per layer
            log.error("%s failed: %s", l.id, e)
    vstats = {}
    if not only or any(v in only for v in VECTOR_META):
        vstats = vectors(force)
        if only:
            vstats = {k: v for k, v in vstats.items() if k in only}
    manifest(rstats, vstats)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    main(a.only.split(",") if a.only else None, a.force)
