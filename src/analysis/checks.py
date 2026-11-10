"""Independent checks of headline numbers (prompt 02, 'Checks before you finish').

Each check recomputes a number by a different route from src/analysis/core.py and compares.
Run: uv run python -m src.analysis.checks
"""
from __future__ import annotations

import json

import geopandas as gpd
import numpy as np
import rioxarray  # noqa: F401
import xarray as xr
from exactextract import exact_extract

from src.analysis.layers import place_polygon
from src.config import BOUNDARY, RASTERS, ROOT, UTM, WARDS, get_logger

log = get_logger("analysis_checks")
OUT = ROOT / "analysis" / "checks.json"


def main() -> dict:
    res = json.loads((ROOT / "analysis" / "results.json").read_text())
    hot_path = RASTERS / "lst_hot_season_median.tif"
    checks = {}

    # 1. County median via rioxarray clip (polygon clip with all_touched=False) vs rasterize mask in core.
    da = xr.open_dataarray(hot_path, engine="rasterio").squeeze()
    county = gpd.read_file(BOUNDARY).to_crs(UTM)
    clip = da.rio.clip(county.geometry, county.crs, drop=True)
    v = clip.values[np.isfinite(clip.values)]
    checks["county_median"] = dict(core=res["q1"]["county_median_c"], independent=round(float(np.median(v)), 1),
                                   method="rioxarray clip of the composite vs rasterio rasterize mask")

    # 2. Hottest and coolest ward medians via exactextract (coverage-weighted) vs cell-centre medians.
    wards = gpd.read_file(WARDS).to_crs(UTM)
    ee = exact_extract(str(hot_path), wards, ["median"], include_cols=["ward_name"], output="pandas")
    ee = ee.set_index("ward_name")["median"]
    for key in ("hottest_ward", "coolest_ward"):
        name = res["q1"][key]
        checks[key] = dict(ward=name, core=res["q1"][f"{key}_c"], independent=round(float(ee[name]), 1),
                           method="exactextract coverage-weighted median vs cell-centre median")
    checks["ward_rank_agreement_spearman"] = None
    import pandas as pd
    ws = pd.read_csv(ROOT / "analysis" / "tables" / "ward_stats.csv").set_index("ward_name")
    from scipy.stats import spearmanr
    checks["ward_rank_agreement_spearman"] = round(float(spearmanr(ws["lst_median_c"], ee.loc[ws.index])[0]), 3)

    # 3. Karura Forest median by reading the raster window directly with numpy.
    import rasterio
    from rasterio.features import geometry_mask
    g = place_polygon("Karura Forest", "forest").geometry
    with rasterio.open(hot_path) as src:
        from rasterio.windows import from_bounds
        win = from_bounds(*g.total_bounds, transform=src.transform).round_offsets().round_lengths()
        a = src.read(1, window=win)
        m = ~geometry_mask(g, out_shape=a.shape, transform=src.window_transform(win))
    vv = a[m & np.isfinite(a)]
    checks["karura_median"] = dict(core=res["q2"]["Karura Forest"]["median_c"], independent=round(float(np.median(vv)), 1),
                                   method="windowed numpy read with geometry_mask vs full-grid mask")

    # 4. Population in the hottest 20 %, recomputed with xarray.
    pop = xr.open_dataarray(RASTERS / "population_30m.tif", engine="rasterio").squeeze()
    popc = pop.rio.clip(county.geometry, county.crs, drop=True)
    hotc = clip
    thr = float(np.nanpercentile(hotc.values, 80))
    p = float(np.nansum(np.where(hotc.values >= thr, popc.values, 0)))
    checks["pop_hottest20"] = dict(core=res["q4"]["pop_in_hottest20"], independent=int(round(p, -3)),
                                   method="xarray clip and threshold vs numpy mask")

    # 5. Spot check: cool places cooler than the CBD and Industrial Area.
    from src.rasterio_utils import polygon_mask, read
    hot = read(hot_path)
    spots = {}
    for name in ["Karura Forest", "Nairobi Arboretum", "Nairobi National Park", "Nairobi Dam", "City Park"]:
        try:
            spots[name] = round(float(np.nanmedian(hot[polygon_mask(place_polygon(name).geometry)])), 1)
        except KeyError:
            spots[name] = None
    hot_ref = min(res["q2"]["CBD"]["median_c"], res["q2"]["Industrial Area"]["median_c"])
    checks["spot_cool_places"] = dict(values=spots, cbd=res["q2"]["CBD"]["median_c"],
                                      industrial=res["q2"]["Industrial Area"]["median_c"],
                                      all_cooler=all(v is not None and v < hot_ref for v in spots.values()))

    # 6. Ward population totals vs county total.
    tot = res["q4"]["county_pop"]
    wsum = float(ws["pop_total"].sum())
    checks["ward_pop_sum"] = dict(ward_sum=int(round(wsum)), county=tot, diff_pct=round(100 * (wsum / tot - 1), 2),
                                  within_5pct=abs(wsum / tot - 1) < 0.05, worldpop_year=2025)

    for k, c in checks.items():
        if isinstance(c, dict) and "core" in c:
            c["match"] = abs(float(c["core"]) - float(c["independent"])) <= (0.15 if "pop" not in k else 0.01 * float(c["core"]))
    # Keep check blocks written by other steps (e.g. "ward_boundaries" from s1b_wards_official).
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    for k in ("ward_boundaries",):
        if k in prev:
            checks[k] = prev[k]
    OUT.write_text(json.dumps(checks, indent=2))
    log.info("Checks: %s", json.dumps(checks))
    return checks


if __name__ == "__main__":
    main()
