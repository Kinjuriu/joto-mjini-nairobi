"""Optional analyses ("if time remains" in prompt 02). Results go to analysis/results_extra.json.

1. Hot-season minus cool-season surface temperature difference map (Nairobi).
2. Kisumu summary, if the Kisumu pipeline outputs exist (run with JOTO_CITY=kisumu for the pipeline).

Run: uv run python -m src.analysis.extras
"""
from __future__ import annotations

import json

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402

from src.analysis.layers import load  # noqa: E402
from src.config import DATA, RASTERS, ROOT, get_logger  # noqa: E402
from src.rasterio_utils import read_grid, write_cog  # noqa: E402

log = get_logger("analysis_extras")
OUT = ROOT / "analysis" / "results_extra.json"
DIVERGING = ["#2F6B8F", "#8CB7CF", "#ECE8E1", "#F1A66B", "#C2401A"]
DIFF_BREAKS = [-15, -3, -1, 1, 3, 15]   # deg C, neutral class centred on zero


def r1(x) -> float:
    return round(float(x), 1)


def season_difference() -> dict:
    L = load()
    t, w, h = read_grid()
    diff = L.hot - L.cool
    write_cog(RASTERS / "lst_hot_minus_cool.tif", diff.astype("float32"), t)
    v = diff[L.county & np.isfinite(diff)]
    rows = []
    for i, wd in L.wards.iterrows():
        m = (L.ward_idx == i + 1) & np.isfinite(diff)
        rows.append(dict(ward_name=wd.ward_name, diff_median_c=r1(np.median(diff[m]))))
    wdf = pd.DataFrame(rows).sort_values("diff_median_c", ascending=False)
    wdf.to_csv(ROOT / "analysis" / "tables" / "ward_hot_minus_cool.csv", index=False)

    # Figure in the project palette.
    from src.analysis.figures import INK, INK2, PAPER, RULE, SANS, SERIF, _save  # noqa: F401
    import geopandas as gpd
    from src.config import PROCESSED, UTM
    county = gpd.read_file(PROCESSED / "nairobi_boundary.geojson").to_crs(UTM)
    ext = [t.c, t.c + w * t.a, t.f + h * t.e, t.f]
    fig = plt.figure(figsize=(12, 7.6))
    ax = fig.add_axes([0.02, 0.1, 0.78, 0.74])
    a = np.where(L.county, np.clip(diff, DIFF_BREAKS[0], DIFF_BREAKS[-1] - 0.01), np.nan)
    ax.imshow(a, cmap=ListedColormap(DIVERGING), norm=BoundaryNorm(DIFF_BREAKS, len(DIVERGING)), extent=ext,
              interpolation="nearest")
    county.boundary.plot(ax=ax, color=INK, linewidth=0.9)
    minx, miny, maxx, maxy = county.total_bounds
    ax.set_xlim(minx - 800, maxx + 800); ax.set_ylim(miny - 800, maxy + 800); ax.set_axis_off()
    lx = fig.add_axes([0.82, 0.32, 0.025, 0.4])
    labels = ["3 or more cooler", "1 to 3 cooler", "within 1", "1 to 3 hotter", "3 or more hotter"]
    for i, c in enumerate(DIVERGING):
        lx.add_patch(plt.Rectangle((0, i), 1, 1, facecolor=c, edgecolor=RULE, linewidth=0.6))
        lx.text(1.4, i + 0.5, labels[i], va="center", size=10)
    lx.set_xlim(0, 1); lx.set_ylim(0, len(DIVERGING)); lx.set_axis_off()
    lx.text(0, len(DIVERGING) + 0.3, "January to March\ncompared with June to August, °C", size=10, color=INK2)
    fig.text(0.04, 0.95, "Almost everywhere, the ground was hotter in January to March", family=SERIF, size=17,
             weight="semibold", va="top")
    fig.text(0.04, 0.895, f"Hot-season minus cool-season median land surface temperature. County median difference "
             f"{np.median(v):.1f} °C.", size=11.5, color=INK2, va="top")
    fig.text(0.04, 0.025, "Source: USGS Landsat 8 and 9 via Microsoft Planetary Computer; hot season 12 scenes 2023 to "
             "2026, cool season 4 scenes 2018 to 2026; analysis: Joto Mjini Nairobi.", size=9, color=INK2)
    _save(fig, "map_hot_minus_cool")
    return dict(county_median_diff_c=r1(np.median(v)), share_hotter_in_hot_season_pct=r1(100 * (v > 0).mean()),
                share_more_than_3c_hotter_pct=r1(100 * (v > 3).mean()),
                largest_diff_wards=wdf.head(5).to_dict("records"), smallest_diff_wards=wdf.tail(5).to_dict("records"),
                caveat="The cool-season composite has only 4 scenes from four different years, so differences partly "
                       "reflect the weather on those days.")


def kisumu_summary() -> dict | None:
    base = DATA / "processed" / "kisumu"
    hot = base / "rasters" / "lst_hot_season_median.tif"
    if not hot.exists():
        return None
    import geopandas as gpd
    import rasterio
    from rasterio.features import rasterize
    with rasterio.open(hot) as src:
        a = src.read(1).astype("float32")
        t = src.transform
    with rasterio.open(base / "rasters" / "tree_fraction_30m.tif") as src:
        tree = src.read(1).astype("float32")
    with rasterio.open(base / "rasters" / "population_30m.tif") as src:
        pop = np.nan_to_num(src.read(1).astype("float32"))
    with rasterio.open(base / "rasters" / "built_fraction_30m.tif") as src:
        built = src.read(1).astype("float32")
    utm = "EPSG:32736"
    county = gpd.read_file(base / "kisumu_boundary.geojson").to_crs(utm)
    wards = gpd.read_file(base / "kisumu_wards.geojson").to_crs(utm).reset_index(drop=True)
    cm = rasterize(county.geometry, out_shape=a.shape, transform=t, fill=0, default_value=1).astype(bool)
    widx = rasterize(((g, i + 1) for i, g in enumerate(wards.geometry)), out_shape=a.shape, transform=t, fill=0,
                     dtype="int32")
    ok = cm & np.isfinite(a)
    v = a[ok]
    rows = []
    for i, wd in wards.iterrows():
        m = (widx == i + 1) & np.isfinite(a)
        if m.sum() < 50:
            continue
        rows.append(dict(ward_name=wd.ward_name, lst_median_c=r1(np.median(a[m])), pop_total=int(round(pop[widx == i + 1].sum(), -2)),
                         tree_pct=r1(100 * np.nanmean(tree[widx == i + 1]))))
    wdf = pd.DataFrame(rows).sort_values("lst_median_c", ascending=False)
    wdf.to_csv(ROOT / "analysis" / "tables" / "kisumu_ward_stats.csv", index=False)
    mb, mt = ok & (built >= 0.75), ok & (tree >= 0.75)
    meta = json.loads((base / "composites_meta.json").read_text())
    return dict(
        study_area="Land area of Kisumu County's 35 wards (DECISIONS D28)",
        hot_season_scenes=meta["hot_season"]["n_scenes"], hot_season_first_year=meta["hot_season"]["first_year"],
        valid_share_pct=r1(100 * ok.sum() / cm.sum()),
        county_median_c=r1(np.median(v)), p10_c=r1(np.percentile(v, 10)), p90_c=r1(np.percentile(v, 90)),
        mostly_built_median_c=r1(np.median(a[mb])) if mb.sum() > 100 else None,
        mostly_tree_median_c=r1(np.median(a[mt])) if mt.sum() > 100 else None,
        pop_total=int(round(pop[cm].sum(), -3)),
        pop_weighted_lst_c=r1(np.average(a[ok], weights=pop[ok])) if pop[ok].sum() > 0 else None,
        hottest_wards=wdf.head(5).to_dict("records"), coolest_wards=wdf.tail(5).to_dict("records"),
    )


def main() -> dict:
    res = dict(season_difference=season_difference())
    k = kisumu_summary()
    if k:
        res["kisumu"] = k
    OUT.write_text(json.dumps(res, indent=2))
    log.info("Extras written: %s", list(res))
    return res


if __name__ == "__main__":
    main()
