"""Step 3: land cover, population, built-up growth and buildings, on the shared grid.

Run: uv run python -m src.pipeline.s3_context [--force] [--only worldcover|population|ghsl|buildings]
"""
from __future__ import annotations

import argparse
import io
import zipfile

import geopandas as gpd
import numpy as np
import planetary_computer
import pystac_client
import rasterio
import requests
from rasterio.transform import Affine
from rasterio.warp import Resampling, reproject
from rasterio.windows import from_bounds

from src.config import BOUNDARY, BUFFER_M, PROCESSED, RASTERS, RAW, UTM, WGS84, get_logger, should_skip
from src.rasterio_utils import county_mask, read_grid, write_cog

log = get_logger("s3_context")

WORLDPOP_YEAR = 2025
WORLDPOP_URL = ("https://data.worldpop.org/GIS/Population/Global_2015_2030/R2025A/{y}/KEN/v1/100m/"
                "constrained/ken_pop_{y}_CN_100m_R2025A_v1.tif")
GHSL_URL = ("https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/"
            "GHS_BUILT_S_E{y}_GLOBE_R2023A_54009_100/V1-0/tiles/"
            "GHS_BUILT_S_E{y}_GLOBE_R2023A_54009_100_V1_0_R10_C22.zip")
GHSL_EPOCHS = [1975, 1990, 2000, 2010, 2020, 2025]
WC_CLASSES = {10: "Tree cover", 20: "Shrubland", 30: "Grassland", 40: "Cropland", 50: "Built-up",
              60: "Bare / sparse vegetation", 70: "Snow and ice", 80: "Permanent water bodies",
              90: "Herbaceous wetland", 95: "Mangroves", 100: "Moss and lichen"}


def _study_bounds_wgs84(margin_deg: float = 0.01):
    b = gpd.read_file(BOUNDARY).to_crs(UTM).buffer(BUFFER_M).to_crs(WGS84).total_bounds
    return b[0] - margin_deg, b[1] - margin_deg, b[2] + margin_deg, b[3] + margin_deg


def worldcover(force: bool = False) -> None:
    out = RASTERS / "worldcover_2021.tif"
    if should_skip(out, force) and (RASTERS / "tree_fraction_30m.tif").exists():
        return
    cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1",
                                    modifier=planetary_computer.sign_inplace)
    items = [i for i in cat.search(collections=["esa-worldcover"], bbox=list(_study_bounds_wgs84())).items()
             if "2021" in i.id]
    if len(items) != 1:
        raise RuntimeError(f"Expected one WorldCover 2021 tile, got {[i.id for i in items]}")
    log.info("WorldCover item %s", items[0].id)
    gt, gw, gh = read_grid()
    # 10 m grid nested exactly in the 30 m grid (3 x 3 sub-cells).
    t10 = Affine(10, 0, gt.c, 0, -10, gt.f)
    wc10 = np.zeros((gh * 3, gw * 3), dtype="uint8")
    with rasterio.open(items[0].assets["map"].href) as src:
        win = from_bounds(*_study_bounds_wgs84(), transform=src.transform).round_offsets().round_lengths()
        data = src.read(1, window=win)
        reproject(data, wc10, src_transform=src.window_transform(win), src_crs=src.crs,
                  dst_transform=t10, dst_crs=UTM, resampling=Resampling.nearest, src_nodata=0, dst_nodata=0)
    write_cog(out, wc10, t10, nodata=0, dtype="uint8")
    blocks = wc10.reshape(gh, 3, gw, 3)
    valid = (blocks > 0).sum(axis=(1, 3))
    for code, name in [(10, "tree"), (50, "built"), (30, "grass"), (60, "bare"), (80, "water")]:
        frac = (blocks == code).sum(axis=(1, 3)) / np.where(valid > 0, valid, np.nan)
        write_cog(RASTERS / f"{name}_fraction_30m.tif", frac.astype("float32"), gt)
    # Majority class on the 30 m grid, for class-level comparisons.
    flat = blocks.transpose(0, 2, 1, 3).reshape(gh, gw, 9)
    codes = np.array(sorted(WC_CLASSES))
    counts = np.stack([(flat == c).sum(axis=2) for c in codes], axis=-1)
    major = codes[counts.argmax(axis=-1)].astype("uint8")
    major[valid == 0] = 0
    write_cog(RASTERS / "worldcover_majority_30m.tif", major, gt, nodata=0, dtype="uint8")
    cm = county_mask()
    for c in (10, 30, 50, 60, 80):
        log.info("WorldCover county share %s: %.1f%%", WC_CLASSES[c], 100 * (major[cm] == c).mean())


def population(force: bool = False) -> None:
    out100 = RASTERS / "population_100m.tif"
    out30 = RASTERS / "population_30m.tif"
    if should_skip(out30, force):
        return
    url = WORLDPOP_URL.format(y=WORLDPOP_YEAR)
    raw = RAW / url.rsplit("/", 1)[1]
    if not raw.exists():
        log.info("Downloading %s", url)
        with requests.get(url, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(raw, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
    with rasterio.open(raw) as src:
        win = from_bounds(*_study_bounds_wgs84(), transform=src.transform).round_offsets().round_lengths()
        pop = src.read(1, window=win).astype("float32")
        nd = src.nodata
        wt = src.window_transform(win)
        crs = src.crs
    pop[(pop == nd) | (pop < 0)] = np.nan
    write_cog(out100, pop, wt, crs=str(crs))
    # Counts to density (people per m2), reproject density, then back to counts per 30 m cell.
    lat = wt.f + wt.e * (np.arange(pop.shape[0]) + 0.5)
    cell_m2 = (abs(wt.a) * 111320 * np.cos(np.radians(lat)))[:, None] * (abs(wt.e) * 110574)
    dens = np.where(np.isnan(pop), 0, pop) / cell_m2
    gt, gw, gh = read_grid()
    d30 = np.zeros((gh, gw), dtype="float32")
    reproject(dens.astype("float32"), d30, src_transform=wt, src_crs=crs, dst_transform=gt, dst_crs=UTM,
              resampling=Resampling.average)
    p30 = d30 * 900.0
    write_cog(out30, p30.astype("float32"), gt)
    county = gpd.read_file(BOUNDARY)
    from rasterio.features import rasterize
    cm100 = rasterize(county.geometry, out_shape=pop.shape, transform=wt, fill=0, default_value=1).astype(bool)
    tot100 = np.nansum(pop[cm100])
    tot30 = p30[county_mask()].sum()
    log.info("WorldPop %d county total: native 100 m %.0f, on 30 m grid %.0f (%.2f%% diff)",
             WORLDPOP_YEAR, tot100, tot30, 100 * (tot30 - tot100) / tot100)


def ghsl(force: bool = False) -> None:
    gt, gw, gh = read_grid()
    # 90 m grid nested in the 30 m grid; close to GHSL's 100 m and keeps alignment.
    t90 = Affine(90, 0, gt.c, 0, -90, gt.f)
    w90, h90 = int(np.ceil(gw / 3)), int(np.ceil(gh / 3))
    for y in GHSL_EPOCHS:
        out = RASTERS / f"ghsl_built_{y}.tif"
        if should_skip(out, force):
            continue
        z = RAW / f"ghsl_built_s_{y}_R10_C22.zip"
        if not z.exists():
            url = GHSL_URL.format(y=y)
            log.info("Downloading %s", url)
            r = requests.get(url, timeout=900)
            r.raise_for_status()
            z.write_bytes(r.content)
        with zipfile.ZipFile(z) as zf:
            name = [n for n in zf.namelist() if n.endswith(".tif")][0]
            tif = RAW / name
            if not tif.exists():
                tif.write_bytes(zf.read(name))
        with rasterio.open(tif) as src:
            # Read a generous window in Mollweide around Nairobi.
            from rasterio.warp import transform_bounds
            mb = transform_bounds(WGS84, src.crs, *_study_bounds_wgs84(0.05))
            win = from_bounds(*mb, transform=src.transform).round_offsets().round_lengths()
            data = src.read(1, window=win).astype("float32")
            if src.nodata is not None:
                data[data == src.nodata] = np.nan
            frac = data / 10000.0  # m2 of built surface per 100 m x 100 m cell -> fraction
            dst = np.full((h90, w90), np.nan, dtype="float32")
            reproject(frac, dst, src_transform=src.window_transform(win), src_crs=src.crs,
                      dst_transform=t90, dst_crs=UTM, resampling=Resampling.bilinear, src_nodata=np.nan,
                      dst_nodata=np.nan)
        write_cog(out, np.clip(dst, 0, 1), t90)
        log.info("GHSL %d built fraction saved", y)


def buildings(force: bool = False) -> None:
    out = PROCESSED / "nairobi_buildings.parquet"
    if should_skip(out, force):
        return
    src = RAW / "overture_buildings.parquet"
    if not src.exists():
        raise FileNotFoundError("Run the Overture download first (see logs/overture_buildings.log)")
    b = gpd.read_parquet(src)
    log.info("Overture buildings in bbox: %d; columns %s", len(b), list(b.columns))
    county = gpd.read_file(BOUNDARY).to_crs(b.crs)
    b = b[b.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
    cent = b.geometry.representative_point()
    inside = cent.within(county.union_all())
    b = b[inside.values].copy()
    bu = b.to_crs(UTM)
    b["footprint_m2"] = bu.area.round(1)

    def _src(s):
        try:
            return s[0]["dataset"] if s is not None and len(s) else None
        except Exception:
            return None

    b["source"] = b["sources"].map(_src) if "sources" in b else None
    keep = ["id", "footprint_m2", "height", "num_floors", "source", "geometry"]
    b = b[[c for c in keep if c in b.columns]]
    b.to_parquet(out)
    log.info("Buildings inside Nairobi County: %d; sources %s", len(b), b["source"].value_counts().to_dict())


def main(force: bool = False, only: str | None = None) -> None:
    steps = {"worldcover": worldcover, "population": population, "ghsl": ghsl, "buildings": buildings}
    for name, fn in steps.items():
        if only and name != only:
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
