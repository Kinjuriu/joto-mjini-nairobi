"""Web-ready outputs for the story site, written to site/public/data/.

Run: uv run python -m src.analysis.web [--only wards|rasters|buildings|charts|places] [--force]
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import Resampling, calculate_default_transform, reproject

from src.analysis.layers import LST_BREAKS, load
from src.config import INTERIM, PROCESSED, RASTERS, ROOT, SITE_DATA, UTM, WEB, WGS84, get_logger, should_skip
from src.rasterio_utils import read, read_grid

log = get_logger("analysis_web")
TABLES = ROOT / "analysis" / "tables"

# Colour ramps fixed in prompts/03_story_site.md.
HEAT = ["#FFF5E6", "#FDD9A8", "#F9B06A", "#EE7D3B", "#D2481E", "#A3200F", "#6B0F0A"]
DIVERGING = ["#2F6B8F", "#8CB7CF", "#ECE8E1", "#F1A66B", "#C2401A"]
GREEN = ["#EEF3E6", "#B9D3A0", "#6FA36A", "#2E6B3F"]
NEUTRAL = ["#F1EEE8", "#C9C2B5", "#8C8475", "#3E3A33"]

ANOMALY_BREAKS = [-12, -4, -1.5, 1.5, 4, 12]      # deg C difference from county median
TREE_BREAKS = [0.1, 0.25, 0.5, 0.75, 1.0001]       # share of cell; under 10 % transparent
BUILT_BREAKS = [0.1, 0.25, 0.5, 0.75, 1.0001]      # GHSL share of cell built; under 10 % transparent
POP_BREAKS = [1000, 5000, 15000, 30000, 1e9]       # people per km2; under 1,000 transparent


def _hex(h: str) -> tuple[int, int, int]:
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def classify(a: np.ndarray, breaks: list[float], colours: list[str], clamp: bool) -> np.ndarray:
    """RGBA uint8 array: class i covers [breaks[i], breaks[i+1]). NaN is transparent."""
    rgba = np.zeros((4,) + a.shape, dtype="uint8")
    b = np.array(breaks, dtype=float)
    x = a.copy()
    if clamp:
        x = np.clip(x, b[0], b[-1] - 1e-6)
    idx = np.digitize(x, b) - 1
    valid = np.isfinite(a) & (idx >= 0) & (idx < len(colours))
    for i, c in enumerate(colours):
        m = valid & (idx == i)
        r, g, bl = _hex(c)
        rgba[0][m], rgba[1][m], rgba[2][m], rgba[3][m] = r, g, bl, 255
    return rgba


def to_pmtiles(rgba: np.ndarray, transform, crs: str, out: Path, name: str) -> None:
    """RGBA array -> EPSG:3857 GeoTIFF -> MBTiles (PNG, with overviews) -> PMTiles."""
    with tempfile.TemporaryDirectory(dir=INTERIM) as td:
        td = Path(td)
        src_tif, merc, mb = td / "src.tif", td / "merc.tif", td / f"{name}.mbtiles"
        h, w = rgba.shape[1:]
        with rasterio.open(src_tif, "w", driver="GTiff", width=w, height=h, count=4, dtype="uint8",
                           crs=crs, transform=transform, photometric="RGB", alpha="YES") as dst:
            dst.write(rgba)
        subprocess.run(["gdalwarp", "-q", "-t_srs", WEB, "-r", "near", "-dstalpha", "-overwrite",
                        "-co", "COMPRESS=DEFLATE", str(src_tif), str(merc)], check=True)
        subprocess.run(["gdal_translate", "-q", "-of", "MBTILES", "-co", "TILE_FORMAT=PNG8",
                        "-co", "ZOOM_LEVEL_STRATEGY=UPPER", "-co", f"NAME={name}", str(merc), str(mb)], check=True)
        subprocess.run(["gdaladdo", "-q", "-r", "nearest", str(mb), "2", "4", "8", "16", "32"], check=True)
        out.unlink(missing_ok=True) if False else None
        if out.exists():
            out.rename(INTERIM / f"_old_{out.name}")
        subprocess.run(["pmtiles", "convert", str(mb), str(out)], check=True, capture_output=True)
    log.info("%s: %.1f MB", out.name, out.stat().st_size / 1e6)


def legend_entry(breaks, colours, unit: str, title: str, clamp: bool, transparent_below: str | None = None) -> dict:
    classes = []
    for i, c in enumerate(colours):
        lo, hi = breaks[i], breaks[i + 1]
        classes.append(dict(colour=c, from_=lo, to=None if hi > 1e8 else min(hi, 1.0) if hi == 1.0001 else hi))
    return dict(title=title, unit=unit, clamp_ends=clamp, classes=classes, transparent_below=transparent_below)


def rasters(force: bool = False) -> None:
    L = load()
    t, _, _ = read_grid()
    county_med = float(np.nanmedian(L.hot[L.county]))
    legends = {}
    jobs = {
        "lst_hot_season": (L.hot, LST_BREAKS, HEAT, True, "deg C", "Land surface temperature, January to March median"),
        "lst_cool_season": (L.cool, LST_BREAKS, HEAT, True, "deg C", "Land surface temperature, June to August median"),
        "lst_anomaly": (L.hot - county_med, ANOMALY_BREAKS, DIVERGING, True, "deg C",
                        f"Difference from the county median ({county_med:.1f} deg C)"),
        "tree_fraction": (L.tree, TREE_BREAKS, GREEN, False, "share of 30 m cell", "Tree cover, ESA WorldCover 2021"),
        "population": (L.pop * (1e6 / 900.0), POP_BREAKS, NEUTRAL, False, "people per km2",
                       "Population density, WorldPop 2025"),
    }
    for name, (a, br, col, clamp, unit, title) in jobs.items():
        out = SITE_DATA / f"{name}.pmtiles"
        a = a.copy()
        a[~np.isfinite(L.hot) & np.isnan(a)] = np.nan
        legends[name] = legend_entry(br, col, unit, title, clamp)
        if should_skip(out, force):
            continue
        to_pmtiles(classify(a, br, col, clamp), t, UTM, out, name)
    from affine import Affine
    t90 = Affine(90, 0, t.c, 0, -90, t.f)
    for yr in (1990, 2020):
        name = f"ghsl_built_{yr}"
        out = SITE_DATA / f"{name}.pmtiles"
        legends[name] = legend_entry(BUILT_BREAKS, NEUTRAL, "share of cell built", f"Built-up surface, GHSL {yr}", False)
        if should_skip(out, force):
            continue
        a = read(RASTERS / f"ghsl_built_{yr}.tif")
        to_pmtiles(classify(a, BUILT_BREAKS, NEUTRAL, False), t90, UTM, out, name)
    legends["_meta"] = dict(county_median_c=round(county_med, 1), lst_breaks=LST_BREAKS,
                            note="Surface temperature layers share the same fixed breaks so they can be compared.")
    # Clean up JSON keys (from_ -> from).
    txt = json.dumps(legends, indent=2).replace('"from_"', '"from"')
    (SITE_DATA / "legends.json").write_text(txt)


def wards(force: bool = False) -> None:
    out = SITE_DATA / "wards.geojson"
    ws = pd.read_csv(TABLES / "ward_stats.csv")
    b = pd.read_parquet(PROCESSED / "buildings_lst.parquet", columns=["ward_id"]) \
        if (PROCESSED / "buildings_lst.parquet").exists() else None
    g = gpd.read_file(PROCESSED / "nairobi_wards.geojson")[["ward_id", "geometry"]]
    g = g.merge(ws, on="ward_id")
    if b is not None:
        nb = b["ward_id"].value_counts()
        g["n_buildings"] = g["ward_id"].map(nb).fillna(0).astype(int)
    else:
        g["n_buildings"] = None
    for c in ["lst_median_c", "lst_p90_c", "lst_anomaly_c", "pop_weighted_lst_c", "cool_lst_median_c"]:
        g[c] = g[c].round(1)
    g["tree_pct"], g["built_pct"] = g["tree_pct"].round(1), g["built_pct"].round(1)
    g["ndvi_median"] = g["ndvi_median"].round(2)
    g["pop_total"] = g["pop_total"].round(-1).astype(int)
    keep = ["ward_id", "ward_name", "lst_median_c", "lst_p90_c", "lst_anomaly_c", "pop_total", "pop_weighted_lst_c",
            "tree_pct", "built_pct", "ndvi_median", "rank_hottest", "rank_pop_weighted", "n_buildings",
            "cool_lst_median_c", "area_km2", "geometry"]
    g = g[keep].to_crs(UTM)
    g["geometry"] = g.geometry.simplify(15, preserve_topology=True)
    g = g.to_crs(WGS84)
    g.to_file(out, driver="GeoJSON", COORDINATE_PRECISION=5)
    log.info("wards.geojson %.2f MB", out.stat().st_size / 1e6)
    gpd.read_file(PROCESSED / "nairobi_boundary.geojson").to_crs(UTM).simplify(20).to_crs(WGS84) \
        .to_frame("geometry").to_file(SITE_DATA / "county.geojson", driver="GeoJSON", COORDINATE_PRECISION=5)


def buildings(force: bool = False) -> None:
    out = SITE_DATA / "buildings.pmtiles"
    sampled = PROCESSED / "buildings_lst.parquet"
    if not should_skip(sampled, force):
        b = gpd.read_parquet(PROCESSED / "nairobi_buildings.parquet").to_crs(UTM)
        pts = b.geometry.representative_point()
        L = load()
        t, w, h = read_grid()
        col = ((pts.x - t.c) / t.a).astype(int).values
        row = ((pts.y - t.f) / t.e).astype(int).values
        ok = (col >= 0) & (col < w) & (row >= 0) & (row < h)
        lst = np.full(len(b), np.nan, dtype="float32")
        lst[ok] = L.hot[row[ok], col[ok]]
        widx = np.zeros(len(b), dtype=int)
        widx[ok] = L.ward_idx[row[ok], col[ok]]
        county_med = float(np.nanmedian(L.hot[L.county]))
        b["lst_c"] = np.round(lst, 1)
        b["lst_anomaly_c"] = np.round(lst - county_med, 1)
        b["ward_id"] = [L.wards.ward_id.iloc[i - 1] if i > 0 else None for i in widx]
        b = b.to_crs(WGS84)
        b[["id", "footprint_m2", "lst_c", "lst_anomaly_c", "ward_id", "geometry"]].to_parquet(sampled)
        log.info("Sampled surface temperature at %d building centroids (%d without a value)", len(b),
                 int(np.isnan(lst).sum()))
    if should_skip(out, force):
        return
    b = gpd.read_parquet(sampled)
    b = b[np.isfinite(b["lst_c"])]
    with tempfile.TemporaryDirectory(dir=INTERIM) as td:
        # tippecanoe 2.79 exited with status 101 on FlatGeobuf input; GeoJSONSeq works.
        fgb = Path(td) / "buildings.geojsonseq"
        b[["lst_c", "lst_anomaly_c", "geometry"]].to_file(fgb, driver="GeoJSONSeq")
        cmd = ["tippecanoe", "-o", str(out), "--force", "-l", "buildings", "-Z12", "-z16",
               "--drop-smallest-as-needed",
               "--simplification=2",
               "-y", "lst_c", "-y", "lst_anomaly_c", "-P", "-q", str(fgb)]
        subprocess.run(cmd, check=True)
    log.info("buildings.pmtiles %.1f MB from %d footprints", out.stat().st_size / 1e6, len(b))


def charts(force: bool = False) -> None:
    for f in ["lst_by_landcover.csv", "lst_by_tree_band.csv", "park_rings.csv", "hot_season_by_year.csv",
              "daily_air_temp_2023_now.csv", "top_wards.csv", "ghsl_built_by_epoch.csv"]:
        shutil.copy(TABLES / f, SITE_DATA / f)
    shutil.copy(PROCESSED / "comparison_areas.geojson", SITE_DATA / "comparison_areas.geojson")


STORY_PLACES = ["Karura Forest", "Nairobi Arboretum", "City Park", "Uhuru Park", "Central Park", "Nairobi National Park",
                "Industrial Area", "Kibera", "Mathare", "Mathare North", "Eastleigh", "Kileleshwa", "Lavington",
                "Kawangware", "Westlands", "Upper Hill", "Embakasi", "Dandora", "Kayole", "Karen", "Kangemi",
                "Mukuru Kwa Njenga", "Mukuru Kwa Ruben", "Mukuru Kayaba Village", "Parklands", "Kilimani",
                "Ngong Road Forest - Section 1", "Nairobi Dam", "South B", "South C", "Ruai", "Kasarani", "Githurai",
                "Huruma", "Kariobangi", "Pumwani", "Umoja", "Donholm", "Buruburu", "Langata", "Runda", "Muthaiga",
                "Gigiri", "Roysambu", "Utawala", "Njiru", "Riruta", "Dagoretti", "Hurlingham", "Ngara", "Pangani"]


def places(force: bool = False) -> None:
    p = gpd.read_file(PROCESSED / "nairobi_places.geojson")
    p = p[p["name"].isin(STORY_PLACES)].copy()
    pu = p.to_crs(UTM)
    p["geometry"] = pu.representative_point().to_crs(WGS84).values
    p["is_green"] = p["kind"].isin(["park", "forest", "nature_reserve", "protected_area"])
    p = p.sort_values("is_green", ascending=False).drop_duplicates("name")
    p[["name", "kind", "is_green", "geometry"]].to_file(SITE_DATA / "places.geojson", driver="GeoJSON",
                                                       COORDINATE_PRECISION=5)
    log.info("places.geojson: %d labels", len(p))


def main(force: bool = False, only: str | None = None) -> None:
    for name, fn in [("buildings", buildings), ("wards", wards), ("rasters", rasters), ("charts", charts),
                     ("places", places)]:
        if only and only != name:
            continue
        try:
            fn(force)
        except Exception as e:
            log.error("%s failed: %s", name, e)
            if only:
                raise


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    main(a.force, a.only)
