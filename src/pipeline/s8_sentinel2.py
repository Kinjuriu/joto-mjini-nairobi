"""Step 8 (v2): Sentinel-2 dry-season composite of Nairobi at 10 m, true and false colour.

Source: Copernicus Sentinel-2 Level-2A (collection `sentinel-2-l2a`, Microsoft Planetary Computer).
Months: January to March 2026 (the 2026 hot, dry season). Per-pixel median of pixels the scene
classification layer (SCL) marks as vegetation (4), bare soil (5) or water (6).

Outputs in data/processed/rasters/:
  s2_2026q1_median.tif   5 bands (B02, B03, B04, B8A, B12), surface reflectance x 10,000, UTM 37S, 10 m
  s2_true_rgb.tif        8-bit RGB, true colour (B04, B03, B02), percentile stretch and gamma
  s2_false_rgb.tif       8-bit RGB, false colour (B12, B8A, B04): vegetation green, built-up purple-grey
  s2_meta.json           scenes and dates used, stretch limits

Run: uv run python -m src.pipeline.s8_sentinel2
"""
from __future__ import annotations

import json

import geopandas as gpd
import numpy as np
import planetary_computer
import pystac_client
import rasterio
from odc.stac import load as odc_load

from src.config import BOUNDARY, RASTERS, UTM, get_logger

log = get_logger("s8_sentinel2")

STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
DATES = "2026-01-01/2026-03-31"
BANDS = ["B02", "B03", "B04", "B8A", "B12"]
CLEAR_SCL = [4, 5, 6]
MAX_DAYS = 14
OUT = RASTERS / "s2_2026q1_median.tif"
META = RASTERS / "s2_meta.json"


def composite() -> None:
    county = gpd.read_file(BOUNDARY)
    bbox = list(county.to_crs(4326).buffer(0.01).total_bounds)   # small margin (degrees)
    cat = pystac_client.Client.open(STAC, modifier=planetary_computer.sign_inplace)
    items = list(cat.search(collections=["sentinel-2-l2a"], bbox=bbox, datetime=DATES,
                            query={"eo:cloud_cover": {"lt": 40}}).items())
    log.info("Sentinel-2 L2A items Jan to Mar 2026 under 40 %% cloud: %d", len(items))
    # Keep the clearest days (a day can have several MGRS tiles).
    by_day: dict[str, list] = {}
    for it in items:
        by_day.setdefault(it.datetime.strftime("%Y-%m-%d"), []).append(it)
    days = sorted(by_day, key=lambda d: np.mean([i.properties["eo:cloud_cover"] for i in by_day[d]]))[:MAX_DAYS]
    use = [i for d in days for i in by_day[d]]
    log.info("Using %d items from %d days: %s", len(use), len(days), ", ".join(sorted(days)))
    # One day at a time, without dask: the first, lazy version stalled on network reads.
    import os
    os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "4")
    os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")
    stacks = {b: [] for b in BANDS}
    ds = None
    for d in sorted(days):
        day = odc_load(by_day[d], bands=BANDS + ["SCL"], crs=UTM, resolution=10, bbox=bbox, groupby="solar_day",
                       resampling={"SCL": "nearest", "*": "bilinear"}, dtype="uint16", nodata=0)
        day = day.isel(time=0)
        clear = day["SCL"].isin(CLEAR_SCL).values
        for b in BANDS:
            v = day[b].values.copy()
            v[~clear] = 0
            stacks[b].append(v)
        ds = day
        log.info("day %s loaded, clear share %.2f", d, float(clear.mean()))
    out = []
    for b in BANDS:
        a = np.stack(stacks[b]).astype("float32")
        a[a == 0] = np.nan
        # Processing baseline 04.00 and later (all 2026 scenes) add 1,000 to reflectance DN.
        out.append(np.nanmedian(a, axis=0) - 1000.0)
        stacks[b] = None
        log.info("median %s done", b)
    arr = np.stack(out).astype("float32")
    t = ds.odc.geobox.affine
    with rasterio.open(OUT, "w", driver="GTiff", width=arr.shape[2], height=arr.shape[1], count=len(BANDS),
                       dtype="uint16", crs=UTM, transform=t, nodata=0, compress="deflate", tiled=True,
                       blockxsize=512, blockysize=512, BIGTIFF="IF_SAFER") as dst:
        dst.write(arr.round().astype("uint16"))
        for i, b in enumerate(BANDS, 1):
            dst.set_band_description(i, b)
    META.write_text(json.dumps(dict(days=sorted(days), n_items=len(use),
                                    items=[i.id for i in use], scl_clear=CLEAR_SCL, months="January to March 2026"),
                               indent=2))
    log.info("Composite written: %s (%d x %d)", OUT, arr.shape[2], arr.shape[1])


def _stretch(a: np.ndarray, lo: float, hi: float, gamma: float) -> np.ndarray:
    x = np.clip((a - lo) / (hi - lo), 0, 1) ** (1 / gamma)
    return (x * 255).round().astype("uint8")


def rgb() -> None:
    with rasterio.open(OUT) as src:
        a = src.read().astype("float32")
        prof = src.profile
    valid = a.sum(0) > 0
    county = gpd.read_file(BOUNDARY).to_crs(UTM)
    meta = json.loads(META.read_text())
    idx = {b: i for i, b in enumerate(BANDS)}
    out = {}
    for name, bands, gamma in (("true", ["B04", "B03", "B02"], 1.45), ("false", ["B12", "B8A", "B04"], 1.1)):
        layers, lims = [], {}
        for b in bands:
            v = a[idx[b]][valid]
            lo, hi = np.percentile(v, [1, 99.5])
            lims[b] = [float(lo), float(hi)]
            layers.append(_stretch(a[idx[b]], lo, hi, gamma))
        rgbarr = np.stack(layers)
        rgbarr = np.maximum(rgbarr, 1)   # 0 is no data, so valid pixels start at 1
        rgbarr[:, ~valid] = 0
        p = prof.copy()
        p.update(count=3, dtype="uint8", nodata=0)
        path = RASTERS / f"s2_{name}_rgb.tif"
        with rasterio.open(path, "w", **p) as dst:
            dst.write(rgbarr)
        out[name] = dict(bands=bands, stretch_percentiles=[1, 99.5], limits=lims, gamma=gamma)
        log.info("%s colour written: %s", name, path)
    meta["stretch"] = out
    META.write_text(json.dumps(meta, indent=2))
    _ = county


if __name__ == "__main__":
    if not OUT.exists():
        composite()
    rgb()
