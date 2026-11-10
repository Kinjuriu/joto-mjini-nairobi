"""Step 2: Landsat 8 and 9 surface temperature and NDVI over the study county (Nairobi by default).

Source: USGS Landsat Collection 2 Level-2, via Microsoft Planetary Computer (no login).
All Nairobi scenes are WRS-2 path 168 row 061, delivered in UTM 37N (EPSG:32637).
UTM 37S (EPSG:32737) is the same projection with a false northing 10,000,000 m larger,
so we read pixels on the native Landsat lattice and relabel them in EPSG:32737 by
adding 10,000,000 m to y. No resampling happens.

Run: uv run python -m src.pipeline.s2_landsat [--force]
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import geopandas as gpd
import numpy as np
import pandas as pd
import planetary_computer
import pystac_client
import rasterio
from rasterio.transform import Affine
from rasterio.windows import Window

from src.config import (BOUNDARY, BUFFER_M, GRID, INTERIM, NAIROBI_TZ, PROCESSED, UTM,
                        get_logger, should_skip)
from src.rasterio_utils import county_mask, write_cog

log = get_logger("s2_landsat")

STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "landsat-c2-l2"
START = "2013-04-01"
NORTH_TO_SOUTH = 10_000_000.0
SCENES = INTERIM / "landsat"
CATALOGUE = PROCESSED / "landsat_scene_catalogue.csv"
QA_MASK_BITS = 0b11111  # bits 0 fill, 1 dilated cloud, 2 cirrus, 3 cloud, 4 cloud shadow
USABLE_CLEAR = 0.80
MIN_COVERAGE = 0.30   # share of the county inside the scene footprint (always 1.0 for Nairobi)


def search(end: str) -> list:
    cat = pystac_client.Client.open(STAC)
    bounds = gpd.read_file(BOUNDARY).total_bounds
    s = cat.search(collections=[COLLECTION], bbox=list(bounds), datetime=f"{START}/{end}",
                   query={"eo:cloud_cover": {"lt": 40},
                          "platform": {"in": ["landsat-8", "landsat-9"]}})
    items = [i for i in s.items() if (i.properties.get("view:sun_elevation") or 0) > 0]
    log.info("STAC search: %d daytime items with scene cloud cover under 40%%", len(items))
    return sorted(items, key=lambda i: i.datetime)


def make_grid(items: list, force: bool = False) -> tuple[Affine, int, int]:
    """Reference 30 m grid in EPSG:32737, on the Landsat pixel lattice, covering county + 2 km."""
    if should_skip(GRID, force):
        with rasterio.open(GRID) as g:
            return g.transform, g.width, g.height
    t = items[0].assets["lwir11"].extra_fields.get("proj:transform") or items[0].properties["proj:transform"]
    x0, y0 = t[2], t[5] + NORTH_TO_SOUTH   # lattice origin in 32737
    minx, miny, maxx, maxy = gpd.read_file(BOUNDARY).to_crs(UTM).buffer(BUFFER_M).total_bounds
    left = x0 + np.floor((minx - x0) / 30) * 30
    right = x0 + np.ceil((maxx - x0) / 30) * 30
    top = y0 - np.floor((y0 - maxy) / 30) * 30
    bottom = y0 - np.ceil((y0 - miny) / 30) * 30
    w, h = int(round((right - left) / 30)), int(round((top - bottom) / 30))
    transform = Affine(30, 0, left, 0, -30, top)
    write_cog(GRID, np.zeros((h, w), dtype="uint8"), transform, nodata=None, dtype="uint8")
    log.info("Grid %d x %d cells, origin (%.0f, %.0f) %s", w, h, left, top, UTM)
    return transform, w, h


def _read_band(href: str, grid_t: Affine, w: int, h: int) -> np.ndarray:
    """Read the grid window from a native 32637 Landsat COG; pad if the scene is smaller."""
    with rasterio.open(href) as src:
        st = src.transform
        assert abs(st.a - 30) < 1e-6 and abs(st.e + 30) < 1e-6
        col0 = (grid_t.c - st.c) / 30
        row0 = (st.f - (grid_t.f - NORTH_TO_SOUTH)) / 30
        if abs(col0 - round(col0)) > 1e-6 or abs(row0 - round(row0)) > 1e-6:
            raise ValueError(f"Scene lattice not aligned with grid: {col0}, {row0}")
        win = Window(int(round(col0)), int(round(row0)), w, h)
        return src.read(1, window=win, boundless=True, fill_value=0)


def process_item(item, grid, cmask: np.ndarray, force: bool) -> dict:
    transform, w, h = grid
    sid = item.id
    lst_path = SCENES / f"{sid}_lst_c.tif"
    ndvi_path = SCENES / f"{sid}_ndvi.tif"
    signed = planetary_computer.sign(item)
    a = signed.assets
    sc = a["lwir11"].extra_fields["raster:bands"][0]
    rf = a["red"].extra_fields["raster:bands"][0]
    st_dn = _read_band(a["lwir11"].href, transform, w, h)
    qa = _read_band(a["qa_pixel"].href, transform, w, h)
    lst = st_dn.astype("float32") * sc["scale"] + sc["offset"] - 273.15
    bad = (st_dn == 0) | ((qa & QA_MASK_BITS) != 0) | (lst < 0) | (lst > 70)
    lst[bad] = np.nan
    clear = (~bad) & cmask
    # Clear share is measured over the part of the county the scene covers. For Nairobi every scene
    # covers the whole county, so this equals the share of the county; for Kisumu (three path/rows)
    # a scene must also cover at least MIN_COVERAGE of the county.
    footprint = (st_dn != 0) & cmask
    coverage = footprint.sum() / cmask.sum()
    clear_frac = clear.sum() / max(footprint.sum(), 1)
    vals = lst[clear]
    dt_utc = item.datetime
    row = dict(scene_id=sid, platform=item.properties["platform"],
               datetime_utc=dt_utc.strftime("%Y-%m-%d %H:%M:%S"),
               datetime_nairobi=dt_utc.astimezone(NAIROBI_TZ).strftime("%Y-%m-%d %H:%M:%S"),
               date=dt_utc.astimezone(NAIROBI_TZ).strftime("%Y-%m-%d"),
               scene_cloud_cover=item.properties.get("eo:cloud_cover"),
               sun_elevation=item.properties.get("view:sun_elevation"),
               coverage_county=round(float(coverage), 4),
               clear_fraction_county=round(float(clear_frac), 4),
               lst_median_c=round(float(np.median(vals)), 2) if vals.size else np.nan,
               lst_p10_c=round(float(np.percentile(vals, 10)), 2) if vals.size else np.nan,
               lst_p90_c=round(float(np.percentile(vals, 90)), 2) if vals.size else np.nan,
               usable=bool(clear_frac >= USABLE_CLEAR and coverage >= MIN_COVERAGE))
    if row["usable"] and (force or not (lst_path.exists() and ndvi_path.exists())):
        red = _read_band(a["red"].href, transform, w, h).astype("float32") * rf["scale"] + rf["offset"]
        nf = a["nir08"].extra_fields["raster:bands"][0]
        nir = _read_band(a["nir08"].href, transform, w, h).astype("float32") * nf["scale"] + nf["offset"]
        with np.errstate(divide="ignore", invalid="ignore"):
            ndvi = (nir - red) / (nir + red)
        ndvi[bad | ~np.isfinite(ndvi) | (ndvi < -1) | (ndvi > 1)] = np.nan
        write_cog(lst_path, lst.astype("float32"), transform)
        write_cog(ndvi_path, ndvi.astype("float32"), transform)
    return row


def main(force: bool = False, end: str | None = None) -> pd.DataFrame:
    SCENES.mkdir(parents=True, exist_ok=True)
    end = end or pd.Timestamp.now(tz=NAIROBI_TZ).strftime("%Y-%m-%d")
    items = search(end)
    grid = make_grid(items, force)
    cmask = county_mask()
    done = pd.read_csv(CATALOGUE) if CATALOGUE.exists() and not force else pd.DataFrame()
    done_ids = set(done["scene_id"]) if len(done) else set()
    todo = [i for i in items if i.id not in done_ids]
    log.info("%d scenes already catalogued, %d to process", len(done_ids), len(todo))
    rows = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(process_item, i, grid, cmask, force): i.id for i in todo}
        for n, f in enumerate(as_completed(futs), 1):
            sid = futs[f]
            try:
                r = f.result()
                rows.append(r)
                log.info("[%d/%d] %s clear %.2f median %s usable %s", n, len(todo), sid,
                         r["clear_fraction_county"], r["lst_median_c"], r["usable"])
            except Exception as e:  # fail soft per scene
                log.warning("[%d/%d] %s failed: %s", n, len(todo), sid, e)
    cat = pd.concat([done, pd.DataFrame(rows)], ignore_index=True)
    cat = cat.sort_values("datetime_utc").reset_index(drop=True)
    cat.to_csv(CATALOGUE, index=False)
    log.info("Catalogue: %d scenes, %d usable", len(cat), int(cat["usable"].sum()))
    return cat


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--end", default=None)
    a = ap.parse_args()
    main(a.force, a.end)
