"""Hot-season land surface temperature at Nairobi's schools.

For each school in data/processed/nairobi_schools.geojson (built by src/pipeline/s10_schools.py):
  - lst_100m_median_c: median of the 30 m hot-season cells (lst_hot_season_median.tif, January to March
    2023 to 2026) whose centres lie within 100 m of the school point. Landsat's thermal band is about 100 m, so
    this is the surface temperature of the area around the school, not of one roof or playground.
  - diff_from_county_median_c: that value minus the county median (the same median as q1.county_median_c).
  - on_hottest_fifth: lst_100m_median_c is at or above the county 80th percentile of hot-season cells (the
    same threshold as q4.hottest20_threshold_c). By definition a fifth of the county's land is at or above it.
  - ward: the IEBC ward containing the point (nearest ward for the few points on the county edge).

Headline numbers count schools for children (pre-primary, primary, secondary, mixed or unknown level). Places
with level "other" (adult education, vocational, tertiary) stay in the table but not in the counts.

Landsat passes over Nairobi at about 10:43 in the morning, during the school day. This is the temperature of
the ground, roofs and roads around the school, not the air temperature in a classroom.

Run: uv run python -m src.analysis.schools
"""
from __future__ import annotations

import json

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import BoundaryNorm  # noqa: E402

from src.analysis.layers import LST_BREAKS, load  # noqa: E402
from src.config import BOUNDARY, FIGURES, PROCESSED, ROOT, SITE_DATA, UTM, WGS84, get_logger, now_local  # noqa: E402
from src.rasterio_utils import read_grid  # noqa: E402

log = get_logger("schools_heat")

SCHOOLS = PROCESSED / "nairobi_schools.geojson"
TABLE = ROOT / "analysis" / "tables" / "schools_heat.csv"
BY_WARD = SITE_DATA / "schools_heat_by_ward.csv"
SITE_SCHOOLS = SITE_DATA / "schools.geojson"
RESULTS = ROOT / "analysis" / "schools_results.json"   # standalone copy
EXTRA = ROOT / "analysis" / "results_extra.json"
FIGURE = FIGURES / "check_schools_hottest_fifth.png"
RADIUS_M = 100.0
CHILD_LEVELS = {"pre-primary", "primary", "secondary", "unknown",
                "pre-primary and primary", "primary and secondary", "pre-primary and primary and secondary"}


def r1(x) -> float:
    return round(float(x), 1)


def lst_around(points: gpd.GeoSeries, hot: np.ndarray, transform) -> tuple[np.ndarray, np.ndarray]:
    """Median of the cells whose centres lie within RADIUS_M of each point, and the number of valid cells."""
    res = transform.a
    k = int(np.ceil(RADIUS_M / res)) + 1
    off = np.arange(-k, k + 1)
    dr, dc = np.meshgrid(off, off, indexing="ij")
    med, n = np.full(len(points), np.nan), np.zeros(len(points), dtype=int)
    inv = ~transform
    for i, p in enumerate(points):
        col, row = inv * (p.x, p.y)
        r0, c0 = int(np.floor(row)), int(np.floor(col))
        rows, cols = r0 + dr, c0 + dc
        cx, cy = transform * (cols + 0.5, rows + 0.5)
        inside = (np.hypot(cx - p.x, cy - p.y) <= RADIUS_M) & (rows >= 0) & (cols >= 0) & \
                 (rows < hot.shape[0]) & (cols < hot.shape[1])
        v = hot[rows[inside], cols[inside]]
        v = v[np.isfinite(v)]
        n[i] = len(v)
        if len(v):
            med[i] = np.median(v)
    return med, n


def main() -> None:
    L = load()
    transform, _, _ = read_grid()
    valid = L.county & np.isfinite(L.hot)
    county_median = float(np.median(L.hot[valid]))
    p80 = float(np.percentile(L.hot[valid], 80))
    log.info("county median %.2f, 80th percentile %.2f", county_median, p80)

    s = gpd.read_file(SCHOOLS).to_crs(UTM)
    s["lst_100m_median_c"], s["n_cells"] = lst_around(s.geometry, L.hot, transform)
    s["diff_from_county_median_c"] = s["lst_100m_median_c"] - county_median
    s["on_hottest_fifth"] = s["lst_100m_median_c"] >= p80

    wards = L.wards[["ward_id", "ward_name", "geometry"]]
    j = gpd.sjoin(s, wards, how="left", predicate="within").drop(columns="index_right")
    j = j[~j.index.duplicated()]
    miss = j["ward_name"].isna()
    if miss.any():
        near = gpd.sjoin_nearest(s[miss], wards, how="left").drop(columns="index_right")
        near = near[~near.index.duplicated()]
        j.loc[miss, ["ward_id", "ward_name"]] = near[["ward_id", "ward_name"]].to_numpy()
    s = j
    s["child_school"] = s["level"].isin(CHILD_LEVELS)
    log.info("schools without a temperature value: %d", int(s["lst_100m_median_c"].isna().sum()))

    ll = s.to_crs(WGS84)
    table = pd.DataFrame({
        "school_id": s.school_id, "name": s.name, "level": s.level, "ownership": s.ownership,
        "sources": s.sources, "location": s.location, "child_school": s.child_school,
        "lon": ll.geometry.x.round(6), "lat": ll.geometry.y.round(6),
        "ward_id": s.ward_id, "ward_name": s.ward_name,
        "lst_100m_median_c": s.lst_100m_median_c.round(2), "n_cells": s.n_cells,
        "diff_from_county_median_c": s.diff_from_county_median_c.round(2),
        "on_hottest_fifth": s.on_hottest_fifth,
    })
    TABLE.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(TABLE, index=False)

    kids = table[table.child_school & table.lst_100m_median_c.notna()]
    by_ward = (kids.groupby(["ward_id", "ward_name"])
               .agg(schools=("school_id", "size"), schools_on_hottest_fifth=("on_hottest_fifth", "sum"),
                    median_school_lst_c=("lst_100m_median_c", "median"))
               .reset_index())
    all_wards = pd.DataFrame(wards.drop(columns="geometry"))
    by_ward = all_wards.merge(by_ward, on=["ward_id", "ward_name"], how="left")
    by_ward[["schools", "schools_on_hottest_fifth"]] = by_ward[["schools", "schools_on_hottest_fifth"]].fillna(0).astype(int)
    by_ward["share_on_hottest_fifth_pct"] = (100 * by_ward.schools_on_hottest_fifth / by_ward.schools.where(by_ward.schools > 0)).round(1)
    by_ward["median_school_lst_c"] = by_ward["median_school_lst_c"].round(1)
    by_ward = by_ward.sort_values(["schools_on_hottest_fifth", "schools"], ascending=False)
    by_ward.to_csv(BY_WARD, index=False)

    def summary(df: pd.DataFrame) -> dict:
        return dict(n_schools=int(len(df)), n_on_hottest_fifth=int(df.on_hottest_fifth.sum()),
                    share_on_hottest_fifth_pct=r1(100 * df.on_hottest_fifth.mean()),
                    share_hotter_than_county_median_pct=r1(100 * (df.diff_from_county_median_c > 0).mean()),
                    median_school_lst_c=r1(df.lst_100m_median_c.median()))

    top10 = by_ward.head(10)
    out = {"schools": {
        **summary(kids),
        "n_by_level": kids.level.value_counts().to_dict(),
        "n_by_ownership": kids.ownership.value_counts().to_dict(),
        "n_places_other_level_excluded": int((~table.child_school).sum()),
        "n_without_temperature": int((table.child_school & table.lst_100m_median_c.isna()).sum()),
        "county_median_c": r1(county_median),
        "hottest_fifth_threshold_c": r1(p80),
        "radius_m": RADIUS_M,
        "top10_wards_by_schools_on_hottest_fifth": [
            dict(ward=r.ward_name, schools=int(r.schools), on_hottest_fifth=int(r.schools_on_hottest_fifth),
                 share_pct=r1(r.share_on_hottest_fifth_pct)) for r in top10.itertuples()],
        "n_wards_with_schools": int((by_ward.schools > 0).sum()),
        "sensitivity_openstreetmap_located_only": summary(kids[kids.location == "OpenStreetMap"]),
        "sensitivity_official_list_only": summary(kids[kids.location != "OpenStreetMap"]),
        "note": ("Surface temperature of the 100 m around each school, hot-season median (January to March 2023 to "
                 "2026), Landsat overpass about 10:43, during the school day. Ground, roofs and roads, not classroom "
                 "air temperature. Counts are schools for children (level 'other' excluded)."),
        "provenance": dict(script="src/analysis/schools.py", schools="data/processed/nairobi_schools.geojson "
                           "(src/pipeline/s10_schools.py)", raster="data/processed/rasters/lst_hot_season_median.tif",
                           table="analysis/tables/schools_heat.csv", by_ward="site/public/data/schools_heat_by_ward.csv",
                           generated=now_local()),
    }}
    RESULTS.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    ex = json.loads(EXTRA.read_text()) if EXTRA.exists() else {}   # keep keys written by other steps
    ex["schools"] = out["schools"]
    EXTRA.write_text(json.dumps(ex, indent=2))
    log.info("schools: %s", json.dumps({k: v for k, v in out["schools"].items() if not isinstance(v, (list, dict))}))

    # Small file for the site: children's schools only, 5 decimal places (about 1 m).
    site = ll[s.child_school.to_numpy()].copy()
    site_out = gpd.GeoDataFrame({
        "id": site.school_id, "name": site.name, "level": site.level, "own": site.ownership,
        "loc": np.where(site.location == "OpenStreetMap", "osm", "official"),
        "lst": site.lst_100m_median_c.round(1), "hot5": site.on_hottest_fifth.astype(int),
    }, geometry=gpd.points_from_xy(site.geometry.x.round(5), site.geometry.y.round(5)), crs=WGS84)
    gj = json.loads(site_out.to_json(drop_id=True))
    for f in gj["features"]:
        f["geometry"]["coordinates"] = [round(c, 5) for c in f["geometry"]["coordinates"]]
    SITE_SCHOOLS.write_text(json.dumps(gj, separators=(",", ":"), ensure_ascii=False))

    figure(L, transform, s, p80)


def figure(L, transform, s: gpd.GeoDataFrame, p80: float) -> None:
    """Check figure: hot-season surface temperature, schools on the hottest fifth in black, others in white."""
    county = gpd.read_file(BOUNDARY).to_crs(UTM)
    xmin, ymin, xmax, ymax = county.total_bounds
    inv = ~transform
    c0, r0 = inv * (xmin, ymax)
    c1, r1_ = inv * (xmax, ymin)
    r0, r1_, c0, c1 = int(r0), int(np.ceil(r1_)), int(c0), int(np.ceil(c1))
    hot = np.where(L.county, L.hot, np.nan)[r0:r1_, c0:c1]
    x0, y0 = transform * (c0, r0)
    x1, y1 = transform * (c1, r1_)
    fig, ax = plt.subplots(figsize=(11, 8), dpi=150)
    cmap = plt.get_cmap("RdYlBu_r", len(LST_BREAKS) + 1)
    im = ax.imshow(hot, extent=(x0, x1, y1, y0), cmap=cmap,
                   norm=BoundaryNorm([10] + LST_BREAKS + [60], cmap.N), interpolation="nearest")
    county.boundary.plot(ax=ax, color="#333", lw=0.8)
    kids = s[s.child_school & s.lst_100m_median_c.notna()]
    cool, hot5 = kids[~kids.on_hottest_fifth], kids[kids.on_hottest_fifth]
    ax.scatter(cool.geometry.x, cool.geometry.y, s=4, c="white", edgecolors="#555", linewidths=0.3,
               label=f"Other schools ({len(cool):,})")
    ax.scatter(hot5.geometry.x, hot5.geometry.y, s=6, c="black", linewidths=0,
               label=f"On the hottest fifth of land, {p80:.1f} °C or more ({len(hot5):,})")
    ax.set_axis_off()
    ax.legend(loc="lower left", fontsize=8, frameon=True)
    cb = fig.colorbar(im, ax=ax, shrink=0.6)
    cb.set_label("Hot-season land surface temperature, °C")
    ax.set_title("Check figure: schools and hot-season land surface temperature, Nairobi County\n"
                 "Median of the 100 m around each school, January to March 2023 to 2026, Landsat about 10:43",
                 fontsize=10)
    fig.text(0.01, 0.01, "Sources: USGS Landsat 8 and 9 (Planetary Computer); Ministry of Education school list "
             "(World Bank, CC BY 4.0); © OpenStreetMap contributors (ODbL). Analysis: Joto Mjini Nairobi.", fontsize=6)
    fig.savefig(FIGURE, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", FIGURE)


if __name__ == "__main__":
    main()
