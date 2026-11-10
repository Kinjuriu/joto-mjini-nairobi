"""Phase 2 analysis: one function per story question. Results go to analysis/results.json.

Run: uv run python -m src.analysis.core
"""
from __future__ import annotations

import json
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
import pymannkendall as mk
from scipy import stats
from shapely.geometry import Point

from src.analysis.layers import load, place_polygon
from src.config import PROCESSED, RASTERS, ROOT, UTM, WGS84, get_logger
from src.pipeline.s2b_composites import BY_YEAR_DIR, META
from src.rasterio_utils import polygon_mask, read, read_grid

log = get_logger("analysis_core")
warnings.filterwarnings("ignore", category=RuntimeWarning)

RESULTS = ROOT / "analysis" / "results.json"
CHARTS = ROOT / "analysis" / "tables"
CHARTS.mkdir(parents=True, exist_ok=True)

# Comparison areas for Q2 (v2), stated exactly so the numbers can be reproduced.
# City centre = the IEBC-based Nairobi Central ward polygon. Industrial Area = the connected group of
# OpenStreetMap landuse=industrial polygons (touching ones merged) that contains or is nearest to the
# OSM place=suburb point "Industrial Area". The v1 circles are kept in data/processed/_old/.
CBD_WARD = "Nairobi Central"
OSM_INDUSTRIAL = ROOT / "data" / "raw" / "osm_industrial" / "industrial.json"
WC_NAMES = {10: "Tree cover", 20: "Shrubland", 30: "Grassland", 40: "Cropland", 50: "Built-up",
            60: "Bare or sparse vegetation", 80: "Water", 90: "Herbaceous wetland"}


def r1(x) -> float:
    return round(float(x), 1)


def _circle(lon: float, lat: float, radius: float) -> gpd.GeoSeries:
    return gpd.GeoSeries([Point(lon, lat)], crs=WGS84).to_crs(UTM).buffer(radius)


# ---------------------------------------------------------------- Q1 and wards
def ward_table() -> pd.DataFrame:
    """Ward statistics on the 30 m grid (cells whose centre is in the ward)."""
    L = load()
    rows = []
    county_med = float(np.nanmedian(L.hot[L.county]))
    for i, w in L.wards.iterrows():
        m = L.ward_idx == i + 1
        v = m & np.isfinite(L.hot)
        hot = L.hot[v]
        pop = L.pop[v]
        rows.append(dict(
            ward_id=w.ward_id, ward_name=w.ward_name, area_km2=w.area_km2,
            n_cells=int(m.sum()), lst_median_c=float(np.median(hot)),
            lst_p90_c=float(np.percentile(hot, 90)),
            pop_total=float(L.pop[m].sum()),
            pop_weighted_lst_c=float(np.average(hot, weights=pop)) if pop.sum() > 0 else np.nan,
            tree_pct=100 * float(np.nanmean(L.tree[m])), built_pct=100 * float(np.nanmean(L.built[m])),
            ndvi_median=float(np.nanmedian(L.ndvi[m])),
            cool_lst_median_c=float(np.nanmedian(L.cool[m])),
        ))
    df = pd.DataFrame(rows)
    df["lst_anomaly_c"] = df["lst_median_c"] - county_med
    df["rank_hottest"] = df["lst_median_c"].rank(ascending=False, method="min").astype(int)
    df["rank_pop_weighted"] = df["pop_weighted_lst_c"].rank(ascending=False, method="min").astype("Int64")
    return df.sort_values("rank_hottest").reset_index(drop=True)


def q1_where_hottest(wards: pd.DataFrame) -> dict:
    L = load()
    v = L.hot[L.county & np.isfinite(L.hot)]
    p10, p90 = np.percentile(v, [10, 90])
    n = len(wards) // 10 or 1
    top, bot = wards.nlargest(n, "lst_median_c"), wards.nsmallest(n, "lst_median_c")
    return dict(
        county_median_c=r1(np.median(v)), county_p10_c=r1(p10), county_p90_c=r1(p90),
        hottest10pct_land_mean_c=r1(v[v >= p90].mean()), coolest10pct_land_mean_c=r1(v[v <= p10].mean()),
        p90_minus_p10_c=r1(p90 - p10),
        n_wards_each_group=n,
        hottest_wards=top[["ward_name", "lst_median_c"]].round(1).to_dict("records"),
        coolest_wards=bot[["ward_name", "lst_median_c"]].round(1).to_dict("records"),
        hottest_wards_mean_c=r1(top["lst_median_c"].mean()), coolest_wards_mean_c=r1(bot["lst_median_c"].mean()),
        ward_gap_c=r1(top["lst_median_c"].mean() - bot["lst_median_c"].mean()),
        hottest_ward=wards.iloc[0]["ward_name"], hottest_ward_c=r1(wards.iloc[0]["lst_median_c"]),
        coolest_ward=wards.iloc[-1]["ward_name"], coolest_ward_c=r1(wards.iloc[-1]["lst_median_c"]),
        cool_season_county_median_c=r1(np.nanmedian(L.cool[L.county])),
        valid_cells_share=r1(100 * np.isfinite(L.hot[L.county]).mean()),
        hot_cool_spearman=round(float(stats.spearmanr(
            L.hot[L.county & np.isfinite(L.hot) & np.isfinite(L.cool)][::7],
            L.cool[L.county & np.isfinite(L.hot) & np.isfinite(L.cool)][::7])[0]), 2),
        hot_cool_ward_spearman=round(float(stats.spearmanr(wards["lst_median_c"], wards["cool_lst_median_c"])[0]), 2),
    )


# ---------------------------------------------------------------- Q2
def _industrial_area() -> tuple[gpd.GeoSeries, list[str]]:
    """Merge touching OSM landuse=industrial polygons; keep the group at the 'Industrial Area' place point."""
    from shapely.ops import unary_union
    from src.pipeline.s1_boundaries import osm_json_to_gdf
    from src.analysis.layers import places
    els = json.loads(OSM_INDUSTRIAL.read_text())["elements"]
    for e in els:   # osm_json_to_gdf skips unnamed features; give every polygon a name so all are kept
        e.setdefault("tags", {}).setdefault("name", f"{e['type']}/{e['id']}")
    g = osm_json_to_gdf(els)
    g = g[g.geom_type.isin(["Polygon", "MultiPolygon"])].to_crs(UTM)
    g["geometry"] = g.buffer(0)
    groups = gpd.GeoSeries(list(unary_union(g.buffer(1.0).geometry).geoms)
                           if unary_union(g.buffer(1.0).geometry).geom_type == "MultiPolygon"
                           else [unary_union(g.buffer(1.0).geometry)], crs=UTM)
    p = places()
    pt = p[(p["name"] == "Industrial Area") & (p["kind"] == "suburb")].geometry.iloc[0]
    best = groups.distance(pt).idxmin()
    grp = groups.iloc[best]
    members = g[g.representative_point().within(grp)]
    return gpd.GeoSeries([unary_union(members.geometry)], crs=UTM), sorted(members["osm_id"].tolist())


def q2_gap() -> dict:
    L = load()
    cbd = L.wards[L.wards["ward_name"] == CBD_WARD].geometry
    ind, ind_ids = _industrial_area()
    areas = {
        "CBD": cbd,
        "Industrial Area": ind,
        "Karura Forest": place_polygon("Karura Forest", "forest").geometry,
        "Nairobi Arboretum": place_polygon("Nairobi Arboretum", "forest").geometry,
    }
    out = {}
    for k, g in areas.items():
        m = polygon_mask(g) & np.isfinite(L.hot)
        out[k] = dict(median_c=r1(np.median(L.hot[m])), mean_c=r1(L.hot[m].mean()), n_cells=int(m.sum()),
                      area_km2=round(float(g.area.sum() / 1e6), 2))
    hot_mean = np.median(np.concatenate([L.hot[polygon_mask(areas[k]) & np.isfinite(L.hot)] for k in ("CBD", "Industrial Area")]))
    cool_mean = np.median(np.concatenate([L.hot[polygon_mask(areas[k]) & np.isfinite(L.hot)] for k in ("Karura Forest", "Nairobi Arboretum")]))
    out["hot_areas_median_c"] = r1(hot_mean)
    out["cool_areas_median_c"] = r1(cool_mean)
    out["gap_c"] = r1(hot_mean - cool_mean)
    out["industrial_minus_karura_c"] = r1(out["Industrial Area"]["median_c"] - out["Karura Forest"]["median_c"])
    out["cbd_minus_arboretum_c"] = r1(out["CBD"]["median_c"] - out["Nairobi Arboretum"]["median_c"])
    out["definitions"] = dict(
        CBD=f"the {CBD_WARD} ward polygon (IEBC-based ward layer)",
        industrial=f"{len(ind_ids)} touching OpenStreetMap landuse=industrial polygons merged into one area "
                   "(the group at the OSM place 'Industrial Area'; ids in analysis/tables/industrial_area_osm_ids.csv)",
        karura="OSM polygon 'Karura Forest' (landuse=forest)",
        arboretum="OSM polygon 'Nairobi Arboretum' (landuse=forest)")
    # Also the gap on the cool-season composite, for the swipe map.
    for k in ("CBD", "Karura Forest"):
        m = polygon_mask(areas[k]) & np.isfinite(L.cool)
        out[k]["cool_season_median_c"] = r1(np.median(L.cool[m]))
    pd.DataFrame({"osm_id": ind_ids}).to_csv(CHARTS / "industrial_area_osm_ids.csv", index=False)
    gpd.GeoDataFrame({"name": list(areas)}, geometry=[g.union_all() for g in areas.values()], crs=UTM) \
        .to_crs(WGS84).to_file(PROCESSED / "comparison_areas.geojson", driver="GeoJSON")
    return out


# ---------------------------------------------------------------- Q3
def q3_landcover() -> dict:
    L = load()
    ok = L.county & np.isfinite(L.hot)
    rows = []
    for code, name in WC_NAMES.items():
        v = L.hot[ok & (L.wc == code)]
        if v.size < 100:
            continue
        rows.append(dict(code=code, landcover=name, n_cells=int(v.size), share_pct=r1(100 * v.size / ok.sum()),
                         median_c=r1(np.median(v)), p25_c=r1(np.percentile(v, 25)), p75_c=r1(np.percentile(v, 75))))
    lc = pd.DataFrame(rows).sort_values("median_c", ascending=False)
    lc.to_csv(CHARTS / "lst_by_landcover.csv", index=False)

    tb = []
    bins = np.arange(0, 1.0001, 0.1)
    okt = ok & np.isfinite(L.tree)
    for lo, hi in zip(bins[:-1], bins[1:]):
        sel = okt & (L.tree >= lo) & ((L.tree < hi) if hi < 1 else (L.tree <= hi))
        v = L.hot[sel]
        tb.append(dict(tree_band=f"{int(lo*100)}-{int(hi*100)}", tree_lo=int(lo * 100), tree_hi=int(hi * 100),
                       n_cells=int(v.size), mean_c=r1(v.mean()), median_c=r1(np.median(v)),
                       p10_c=r1(np.percentile(v, 10)), p25_c=r1(np.percentile(v, 25)),
                       p75_c=r1(np.percentile(v, 75)), p90_c=r1(np.percentile(v, 90))))
    tb = pd.DataFrame(tb)
    tb.to_csv(CHARTS / "lst_by_tree_band.csv", index=False)

    mostly_built = ok & (L.built >= 0.75)
    mostly_tree = ok & (L.tree >= 0.75)
    nd = ok & np.isfinite(L.ndvi)
    rho, _ = stats.spearmanr(L.ndvi[nd][::7], L.hot[nd][::7])
    rho_t, _ = stats.spearmanr(L.tree[okt][::7], L.hot[okt][::7])
    built_med, tree_med = np.median(L.hot[mostly_built]), np.median(L.hot[mostly_tree])
    return dict(
        by_class=lc.to_dict("records"),
        mostly_built_median_c=r1(built_med), mostly_tree_median_c=r1(tree_med),
        built_minus_tree_c=r1(built_med - tree_med),
        mostly_built_cells=int(mostly_built.sum()), mostly_tree_cells=int(mostly_tree.sum()),
        tree_band_0_10_mean_c=tb.iloc[0]["mean_c"], tree_band_90_100_mean_c=tb.iloc[-1]["mean_c"],
        tree_band_gap_c=r1(tb.iloc[0]["mean_c"] - tb.iloc[-1]["mean_c"]),
        spearman_ndvi_lst=round(float(rho), 2), spearman_tree_lst=round(float(rho_t), 2),
        note="Spearman correlations on every 7th valid county cell (spatial autocorrelation means p-values are not meaningful)",
    )


# ---------------------------------------------------------------- Q4
def q4_exposure(wards: pd.DataFrame) -> dict:
    L = load()
    ok = L.county & np.isfinite(L.hot)
    p80 = np.percentile(L.hot[ok], 80)
    hot20 = ok & (L.hot >= p80)
    pop_tot = L.pop[L.county].sum()
    pop_hot = L.pop[hot20].sum()
    pw = float(np.average(L.hot[ok], weights=L.pop[ok]))
    top = wards.dropna(subset=["pop_weighted_lst_c"]).nlargest(10, "pop_weighted_lst_c")
    top_out = top[["ward_name", "pop_weighted_lst_c", "lst_median_c", "pop_total", "tree_pct"]].copy()
    top_out.to_csv(CHARTS / "top_wards.csv", index=False)
    return dict(
        hottest20_threshold_c=r1(p80), pop_in_hottest20=int(round(pop_hot, -3)),
        pop_in_hottest20_exact=float(pop_hot),
        pop_share_in_hottest20_pct=r1(100 * pop_hot / pop_tot), county_pop=int(round(pop_tot)),
        land_share_pct=20.0,
        pop_weighted_county_lst_c=r1(pw), area_weighted_county_mean_c=r1(L.hot[ok].mean()),
        top10_pop_weighted=[dict(ward_name=r.ward_name, pop_weighted_lst_c=r1(r.pop_weighted_lst_c),
                                 pop_total=int(round(r.pop_total, -2))) for r in top.itertuples()],
        top10_total_pop=int(round(top["pop_total"].sum(), -3)),
        top10_max_tree_pct=r1(top["tree_pct"].max()),
    )


# ---------------------------------------------------------------- Q5
def q5_park_rings() -> dict:
    L = load()
    from src.analysis.layers import places
    p = places()
    green = p[p["kind"].isin(["park", "forest", "nature_reserve", "protected_area"]) &
              p.geom_type.isin(["Polygon", "MultiPolygon"])].union_all()
    green_mask = polygon_mask(gpd.GeoSeries([green], crs=UTM))
    ok = L.county & np.isfinite(L.hot) & (L.built >= 0.5) & ~green_mask & (L.tree < 0.3)
    rows, summary = [], {}
    for name in ["Karura Forest", "Nairobi Arboretum", "City Park"]:
        poly = place_polygon(name).geometry.union_all()
        inside = polygon_mask(gpd.GeoSeries([poly], crs=UTM))
        park_med = r1(np.nanmedian(L.hot[inside]))
        prev = poly
        ring_vals = []
        for d in range(100, 1001, 100):
            outer = poly.buffer(d)
            ring = outer.difference(prev)
            prev = outer
            m = polygon_mask(gpd.GeoSeries([ring], crs=UTM)) & ok
            v = L.hot[m]
            row = dict(park=name, ring_from_m=d - 100, ring_to_m=d, n_cells=int(m.sum()),
                       median_c=r1(np.median(v)) if v.size >= 20 else np.nan,
                       mean_c=r1(v.mean()) if v.size >= 20 else np.nan, park_median_c=park_med)
            rows.append(row)
            ring_vals.append(row["median_c"])
        rv = np.array(ring_vals, dtype=float)
        far = np.nanmean(rv[-3:])  # 700 to 1,000 m: reference band
        # Distance where the ring is within 0.5 C of the far band.
        reach = next((100 * (i + 1) for i, x in enumerate(rv) if np.isfinite(x) and x >= far - 0.5), None)
        summary[name] = dict(park_median_c=park_med, ring_0_100_c=r1(rv[0]), ring_700_1000_c=r1(far),
                             near_minus_far_c=r1(rv[0] - far), reach_m=reach,
                             monotonic_increase=bool(np.all(np.diff(rv[np.isfinite(rv)]) >= -0.3)))
    df = pd.DataFrame(rows)
    df.to_csv(CHARTS / "park_rings.csv", index=False)
    return dict(parks=summary, method="Built-up cells (WorldCover built-up share >= 50 %, tree share < 30 %) outside all OSM parks and forests, in 100 m rings out to 1,000 m from the park edge; medians of hot-season surface temperature; 'reach' is the first ring within 0.5 C of the 700 to 1,000 m band.")


# ---------------------------------------------------------------- Q6
def q6_trend() -> dict:
    L = load()
    meta = json.loads(META.read_text())
    rows = []
    for y, info in sorted(meta["by_year"].items(), key=lambda kv: int(kv[0])):
        a = read(BY_YEAR_DIR / f"{y}.tif")
        v = a[L.county & np.isfinite(a)]
        rows.append(dict(year=int(y), n_scenes=info["n_scenes"], county_median_c=r1(np.median(v)),
                         valid_share_pct=r1(100 * v.size / L.county.sum()), dates=";".join(info["dates"])))
    df = pd.DataFrame(rows)
    df.to_csv(CHARTS / "hot_season_by_year.csv", index=False)
    res = mk.original_test(df["county_median_c"].values)
    ts = stats.theilslopes(df["county_median_c"].values, df["year"].values)
    # GHSL built-up area inside the county.
    t, w, h = read_grid()
    from affine import Affine
    from rasterio.features import rasterize
    from src.config import BOUNDARY
    county = gpd.read_file(BOUNDARY).to_crs(UTM)
    t90 = Affine(90, 0, t.c, 0, -90, t.f)
    built = {}
    for yr in (1975, 1990, 2000, 2010, 2020, 2025):
        a = read(RASTERS / f"ghsl_built_{yr}.tif")
        cm = rasterize(county.geometry, out_shape=a.shape, transform=t90, fill=0, default_value=1).astype(bool)
        built[yr] = r1(np.nansum(a[cm]) * 90 * 90 / 1e6)
    gb = pd.DataFrame({"epoch": list(built), "built_km2": list(built.values())})
    gb["projection"] = gb["epoch"] > 2020
    gb.to_csv(CHARTS / "ghsl_built_by_epoch.csv", index=False)
    return dict(
        years=df[["year", "n_scenes", "county_median_c"]].to_dict("records"),
        mann_kendall_trend=res.trend, mann_kendall_p=round(float(res.p), 3),
        theil_sen_slope_c_per_decade=r1(ts.slope * 10),
        theil_sen_ci_c_per_decade=[r1(ts.low_slope * 10), r1(ts.high_slope * 10)],
        clear_trend=bool(res.p < 0.05),
        built_km2=built, built_growth_1990_2020_km2=r1(built[2020] - built[1990]),
        built_ratio_2020_1990=round(built[2020] / built[1990], 2),
        built_share_county_1990_pct=r1(100 * built[1990] / (county.area.sum() / 1e6)),
        built_share_county_2020_pct=r1(100 * built[2020] / (county.area.sum() / 1e6)),
    )


# ---------------------------------------------------------------- Q7
def q7_inequality(wards: pd.DataFrame) -> dict:
    w = wards.dropna(subset=["pop_weighted_lst_c"]).sort_values("pop_weighted_lst_c", ascending=False)
    n = int(round(len(w) / 5))
    hot, cool = w.head(n), w.tail(n)

    def grp(g):
        return dict(n_wards=len(g), pop=int(round(g["pop_total"].sum(), -3)),
                    pop_weighted_lst_c=r1(np.average(g["pop_weighted_lst_c"], weights=g["pop_total"])),
                    tree_pct=r1(np.average(g["tree_pct"], weights=g["area_km2"])),
                    built_pct=r1(np.average(g["built_pct"], weights=g["area_km2"])),
                    pop_density_per_km2=int(round(g["pop_total"].sum() / g["area_km2"].sum(), -2)),
                    wards=g["ward_name"].tolist())
    h, c = grp(hot), grp(cool)
    return dict(hottest_fifth=h, coolest_fifth=c,
                lst_gap_c=r1(h["pop_weighted_lst_c"] - c["pop_weighted_lst_c"]),
                tree_ratio=round(c["tree_pct"] / h["tree_pct"], 1) if h["tree_pct"] > 0 else None,
                settlement_comparison="not done: no open informal settlement layer could be downloaded (DECISIONS D9)")


# ---------------------------------------------------------------- Q8
def q8_air() -> dict:
    a = pd.read_csv(PROCESSED / "nairobi_daily_air_temp.csv", parse_dates=["date"])
    base = a[(a["date"] >= "1991-01-01") & (a["date"] <= "2020-12-31")]
    p90 = float(np.percentile(base["temperature_2m_max"], 90))
    r = a[a["date"] >= "2023-01-01"].copy()
    r["dtmax"] = r["temperature_2m_max"].diff().abs()
    r["el_nino"] = r["date"] >= "2026-05-01"
    r["above_p90"] = r["temperature_2m_max"] > p90
    r[["date", "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean", "el_nino"]] \
        .to_csv(CHARTS / "daily_air_temp_2023_now.csv", index=False, date_format="%Y-%m-%d")
    per_year = r.groupby(r["date"].dt.year).agg(days=("date", "size"), above_p90=("above_p90", "sum")).reset_index()
    # El Nino months vs the same calendar months in 1991 to 2020.
    en = r[r["el_nino"]]
    months = sorted(en["date"].dt.month.unique())
    clim = base[base["date"].dt.month.isin(months)]
    en_mean, clim_mean = en["temperature_2m_max"].mean(), clim["temperature_2m_max"].mean()
    big = int((r["dtmax"] >= 3).sum())
    return dict(
        p90_tmax_1991_2020_c=r1(p90), mean_abs_daily_change_tmax_c=r1(r["dtmax"].mean()),
        days_change_3c_or_more=big, share_days_change_3c_or_more_pct=r1(100 * big / r["dtmax"].notna().sum()),
        max_daily_change_c=r1(r["dtmax"].max()),
        days_above_p90_by_year=per_year.to_dict("records"),
        el_nino_period=f"{en['date'].min().date()} to {en['date'].max().date()}",
        el_nino_mean_tmax_c=r1(en_mean), same_months_1991_2020_mean_tmax_c=r1(clim_mean),
        el_nino_minus_clim_c=r1(en_mean - clim_mean),
        tmax_2023_now_max_c=r1(r["temperature_2m_max"].max()),
        tmax_2023_now_max_date=str(r.loc[r["temperature_2m_max"].idxmax(), "date"].date()),
        last_date=str(r["date"].max().date()),
    )


# ---------------------------------------------------------------- Story extras
PAIR = ("Kileleshwa", "Kawangware")   # neighbouring wards with contrasting tree cover (chapter 5)


def q9_pair(wards: pd.DataFrame) -> dict:
    out = {}
    for name in PAIR:
        r = wards[wards["ward_name"] == name].iloc[0]
        out[name] = dict(lst_median_c=r1(r.lst_median_c), tree_pct=r1(r.tree_pct), built_pct=r1(r.built_pct),
                         pop_total=int(round(r.pop_total, -2)), area_km2=r1(r.area_km2),
                         pop_density_per_km2=int(round(r.pop_total / r.area_km2, -2)),
                         rank_hottest=int(r.rank_hottest))
    a, b = out[PAIR[1]], out[PAIR[0]]
    out["lst_gap_c"] = r1(a["lst_median_c"] - b["lst_median_c"])
    # Do the two wards share a boundary?
    g = load().wards.set_index("ward_name").geometry
    out["share_boundary"] = bool(g[PAIR[0]].buffer(30).intersects(g[PAIR[1]]))
    out["distance_km"] = r1(g[PAIR[0]].distance(g[PAIR[1]]) / 1000)
    out["centroid_distance_km"] = r1(g[PAIR[0]].centroid.distance(g[PAIR[1]].centroid) / 1000)
    return out


def q0_data() -> dict:
    from src.pipeline.s2_landsat import CATALOGUE
    cat = pd.read_csv(CATALOGUE)
    meta = json.loads(META.read_text())
    hs = cat[cat["scene_id"].isin(meta["hot_season"]["scenes"])]
    t = pd.to_datetime(hs["datetime_nairobi"])
    mins = (t.dt.hour * 60 + t.dt.minute).mean()
    return dict(n_scenes_searched=len(cat), n_scenes_usable=int(cat["usable"].sum()),
                first_scene=str(pd.to_datetime(cat["date"]).min().date()),
                last_scene=str(pd.to_datetime(cat["date"]).max().date()),
                n_hot_scenes=meta["hot_season"]["n_scenes"], n_cool_scenes=meta["cool_season"]["n_scenes"],
                cool_first_year=meta["cool_season"]["first_year"],
                overpass_local=f"{int(mins // 60)}:{int(mins % 60):02d}",
                usable_hot_months_share_pct=r1(100 * cat[cat["usable"]]["date"].str[5:7].isin(["01", "02", "03"]).mean()),
                n_wards=len(load().wards))


def main() -> dict:
    wards = ward_table()
    wards.to_csv(CHARTS / "ward_stats.csv", index=False)
    results = dict(
        q1=q1_where_hottest(wards), q2=q2_gap(), q3=q3_landcover(), q4=q4_exposure(wards),
        q5=q5_park_rings(), q6=q6_trend(), q7=q7_inequality(wards), q8=q8_air(),
        q9=q9_pair(wards), q0=q0_data(),
        composites=json.loads(META.read_text()),
    )
    RESULTS.write_text(json.dumps(results, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    log.info("Results written to %s", RESULTS)
    return results


if __name__ == "__main__":
    main()
