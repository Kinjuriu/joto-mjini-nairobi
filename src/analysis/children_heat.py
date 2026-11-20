"""People, school-age children and tree cover near schools on Nairobi's hot and cool ground (D59).

Heat bands use the same layer and thresholds as q1 and q4: the hot-season median land surface temperature
(lst_hot_season_median.tif, January to March mornings 2023 to 2026) on the shared 30 m grid. County land with a
temperature is split into fifths by its own 20th, 40th, 60th and 80th percentiles, and into a hotter and a
cooler half at the county median (q1.county_median_c). People are the WorldPop 2025 layer already used on the
site (population_30m.tif), so "people on the hottest fifth" equals q4.pop_in_hottest20.

Children by age. WorldPop's age-and-sex layers could not be downloaded (the network blocks worldpop.org), so
each 30 m cell's people are split by age with the 2019 census age mix of the census sub-county its ward belongs
to (KNBS Volume III, single years of age, Kinjuriu/kenya-2019-census-csv at commit CENSUS_COMMIT). Wards are
linked to the 11 census sub-counties as in D55 (analysis/tables/ward_population_scaled.csv); the few cells inside
the county boundary but outside every ward use the county's age mix. Inside one census sub-county every cell
therefore has the same share of children, so differences between the hot and cool sides come only from
differences between sub-counties. WorldPop's own age layers are built in a similar way, from census age shares
for administrative areas, so the result should be close; it is an estimate.

School levels follow the Competency-Based Curriculum entry ages used in the census repository: pre-primary 4 to
5, primary 6 to 11, junior school 12 to 14, senior school 15 to 17. "School-going" applies Nairobi County's
2019 attendance rates by age group (Volume IV table 2.6b: ages 4 to 5, 6 to 13 and 14 to 17) to each single
year of age. It is a rough estimate: the census gives these rates for the county only.

Sensitivity: the same counts after scaling WorldPop to census sub-county totals grown to 2025 (D55 factors).

Trees near schools: mean tree fraction (tree_fraction_30m.tif, ESA WorldCover 2021) of the 30 m cells whose
centres lie within 200 m of each school for children, compared between schools on the hotter and cooler halves
and on the hottest and coolest fifths (school temperature from analysis/tables/schools_heat.csv).

Outputs: analysis/tables/people_by_heat.csv, children_by_heat.csv, children_by_ward.csv, schools_trees_200m.csv,
analysis/children_heat_results.json (standalone copy) and the keys people_by_heat, children_by_heat and
schools_trees_200m in analysis/results_extra.json.

Run: uv run python -m src.analysis.children_heat
"""
from __future__ import annotations

import json

import geopandas as gpd
import numpy as np
import pandas as pd

from src.analysis.layers import load
from src.config import ROOT, UTM, WGS84, get_logger, now_local
from src.rasterio_utils import read_grid

log = get_logger("children_heat")

CENSUS = ROOT / "data" / "raw" / "census_2019"
CENSUS_COMMIT = "d05f526fd31801306a009f7b3e5d25a72b426bf6"
AGE = CENSUS / "kenya_2019_census_population_by_age_sex_county_subcounty.csv"
SCHOOL_AGE = CENSUS / "kenya_2019_census_school_age_population_by_county_subcounty.csv"
ATT_AGE = CENSUS / "kenya_2019_census_school_attendance_by_age_group_county.csv"
ROOFS = CENSUS / "kenya_2019_census_roofing_material_by_county_subcounty.csv"
SITE_DATA = ROOT / "site" / "public" / "data"
TABLES = ROOT / "analysis" / "tables"
WARD_SC = TABLES / "ward_population_scaled.csv"
SCHOOLS = TABLES / "schools_heat.csv"
EXTRA = ROOT / "analysis" / "results_extra.json"
STANDALONE = ROOT / "analysis" / "children_heat_results.json"
COUNTY = "NAIROBI"
TREE_RADIUS_M = 200.0

BANDS = {  # name: (first age, last age), inclusive
    "pre_primary_4_5": (4, 5),
    "primary_6_11": (6, 11),
    "junior_school_12_14": (12, 14),
    "senior_school_15_17": (15, 17),
    "school_age_4_17": (4, 17),
    "under_4": (0, 3),
    "adults_18_plus": (18, 200),
}
FIFTHS = ["coolest fifth", "second fifth", "middle fifth", "fourth fifth", "hottest fifth"]


def r1(x) -> float:
    return round(float(x), 1)


def k(x) -> int:
    """People counts rounded to the nearest thousand for display."""
    return int(round(float(x), -3))


def age_shares() -> pd.DataFrame:
    """Share of each census area's age-stated population at each single year of age (rows: area, cols: age)."""
    d = pd.read_csv(AGE)
    d = d[(d.county == "NAIROBI CITY") & (d.age_kind == "single")].copy()
    d["a"] = d["age"].replace({"100+": "100"}).astype(int)
    tab = d.pivot_table(index="area", columns="a", values="total", aggfunc="sum").fillna(0)
    return tab.div(tab.sum(axis=1), axis=0)


def attendance_by_age() -> pd.Series:
    """Nairobi County share 'at school now' by single year of age 4 to 17 (Volume IV table 2.6b)."""
    d = pd.read_csv(ATT_AGE)
    d = d[d.county == "NAIROBI CITY"].set_index("breakdown")
    rate = {g: d.loc[g, "at_school_total"] / d.loc[g, "total_total"] for g in ["age_4-5", "age_6-13", "age_14-17"]}
    s = pd.Series(0.0, index=range(0, 101))
    s[4:5] = rate["age_4-5"]
    s[6:13] = rate["age_6-13"]
    s[14:17] = rate["age_14-17"]
    return s


def main() -> dict:
    L = load()
    shares = age_shares()
    att = attendance_by_age()
    areas = list(shares.index)                       # 11 sub-counties + NAIROBI
    ages = np.array(shares.columns)

    # per-person factors for each area and band, and school-going factors
    fac = {b: np.array([shares.loc[a, (ages >= lo) & (ages <= hi)].sum() for a in areas]) for b, (lo, hi) in BANDS.items()}
    att_v = att.reindex(ages).fillna(0).values
    going = {b: np.array([(shares.loc[a].values * att_v * ((ages >= lo) & (ages <= hi))).sum() for a in areas])
             for b, (lo, hi) in BANDS.items() if b not in ("under_4", "adults_18_plus")}

    # cell -> census area index
    ws = pd.read_csv(WARD_SC)
    w2sc = dict(zip(ws.ward_name, ws.census_subcounty))
    w2f = dict(zip(ws.ward_name, ws.scale_factor))
    county_scale = float(ws.census_subcounty_2025_grown.drop_duplicates().sum() / ws.pop_worldpop2025.sum())
    ward_area = np.array([areas.index(COUNTY)] + [areas.index(w2sc[n]) for n in L.wards.ward_name])
    ward_scale = np.array([county_scale] + [w2f[n] for n in L.wards.ward_name])
    area_idx = ward_area[L.ward_idx]
    scale = ward_scale[L.ward_idx]

    county = L.county
    ok = county & np.isfinite(L.hot)
    q = np.percentile(L.hot[ok], [20, 40, 60, 80])
    med = float(np.nanmedian(L.hot[county]))
    fifth = np.full(L.hot.shape, -1, dtype=int)
    fifth[ok] = np.digitize(L.hot[ok], q)
    half = np.full(L.hot.shape, "", dtype=object)
    half[ok & (L.hot > med)] = "hotter half"
    half[ok & (L.hot <= med)] = "cooler half"

    pop = L.pop
    pop_county = float(pop[county].sum())
    cells = {b: pop * fac[b][area_idx] for b in BANDS}
    cells_going = {b: pop * going[b][area_idx] for b in going}
    cells_scaled = {b: pop * scale * fac[b][area_idx] for b in BANDS}

    groups = [(FIFTHS[i], county & (fifth == i)) for i in range(5)]
    groups += [("hotter half", county & (half == "hotter half")), ("cooler half", county & (half == "cooler half")),
               ("no temperature", county & ~np.isfinite(L.hot)), ("county", county)]
    land_ok = ok.sum()
    rows = []
    for name, m in groups:
        row = dict(group=name, land_share_pct=r1(100 * m.sum() / land_ok) if name not in ("no temperature", "county") else None,
                   people=float(pop[m].sum()))
        for b in BANDS:
            row[b] = float(cells[b][m].sum())
            row[b + "_scaled"] = float(cells_scaled[b][m].sum())
        for b in going:
            row[b + "_school_going"] = float(cells_going[b][m].sum())
        rows.append(row)
    t = pd.DataFrame(rows).set_index("group")
    for c in ["people"] + list(BANDS):
        t[c + "_share_of_county_pct"] = (100 * t[c] / t.loc["county", c]).round(1)
    t["children_4_17_per_100_people"] = (100 * t["school_age_4_17"] / t["people"]).round(1)
    out = t.reset_index()
    num = out.select_dtypes("number").columns
    out[num] = out[num].round(1)
    out.to_csv(TABLES / "children_by_heat.csv", index=False)
    pbh = out[["group", "land_share_pct", "people", "people_share_of_county_pct"]]
    pbh.to_csv(TABLES / "people_by_heat.csv", index=False)

    # ---------- checks
    # the CSV's data rows carry five more fields than its header (school-age male, female, total, share, page),
    # so read by position: column 3 is total population, column 18 is school-age total
    sa = pd.read_csv(SCHOOL_AGE, header=None, skiprows=1)
    nb = sa[(sa[0] == "county") & (sa[1] == "NAIROBI CITY")].iloc[0]
    census_share = 100 * float(nb[18]) / float(nb[3])
    chk = dict(
        land_fifths_each_about_20pct=bool(all(abs(t.loc[f, "land_share_pct"] - 20) < 0.2 for f in FIFTHS)),
        hottest_fifth_people_equals_q4=bool(abs(t.loc["hottest fifth", "people"] - 827100.625) < 1),
        fifths_plus_no_temp_equal_county=bool(abs(t.loc[FIFTHS, "people"].sum() + t.loc["no temperature", "people"] - pop_county) < 1),
        halves_equal_fifths=bool(abs(t.loc[["hotter half", "cooler half"], "people"].sum() - t.loc[FIFTHS, "people"].sum()) < 1),
        bands_add_up=bool(abs(sum(t.loc["county", b] for b in ["pre_primary_4_5", "primary_6_11", "junior_school_12_14", "senior_school_15_17"]) - t.loc["county", "school_age_4_17"]) < 1),
        all_ages_add_up=bool(abs(t.loc["county", "under_4"] + t.loc["county", "school_age_4_17"] + t.loc["county", "adults_18_plus"] - pop_county) < 1),
        census_school_age_share_pct=r1(census_share),
        modelled_school_age_share_pct=r1(100 * t.loc["county", "school_age_4_17"] / pop_county),
    )
    # independent path: hot-half children summed area by area from people totals
    alt = 0.0
    for i, a in enumerate(areas):
        m = county & (half == "hotter half") & (area_idx == i)
        alt += pop[m].sum() * fac["school_age_4_17"][i]
    chk["hot_half_children_independent_match"] = bool(abs(alt - t.loc["hotter half", "school_age_4_17"]) < 1)
    log.info("checks: %s", chk)

    # ---------- wards
    wrows = []
    for i, n in enumerate(L.wards.ward_name, start=1):
        m = county & (L.ward_idx == i)
        wrows.append(dict(ward_name=n, census_subcounty=w2sc[n], people=k(pop[m].sum()),
                          **{b: int(round(cells[b][m].sum(), -2)) for b in BANDS if b not in ("under_4", "adults_18_plus")},
                          school_going_4_17=int(round(cells_going["school_age_4_17"][m].sum(), -2)),
                          share_people_on_hotter_half_pct=r1(100 * pop[m & (half == "hotter half")].sum() / max(pop[m].sum(), 1)),
                          lst_median_c=r1(np.nanmedian(L.hot[m]))))
    pd.DataFrame(wrows).sort_values("lst_median_c", ascending=False).to_csv(TABLES / "children_by_ward.csv", index=False)

    # ---------- trees within 200 m of schools
    s = pd.read_csv(SCHOOLS)
    s = s[s.child_school & s.lst_100m_median_c.notna()].copy()
    g = gpd.GeoSeries(gpd.points_from_xy(s.lon, s.lat), crs=WGS84).to_crs(UTM)
    tr, w, h = read_grid()
    res = tr.a
    rad = int(np.ceil(TREE_RADIUS_M / res)) + 1
    off = np.arange(-rad, rad + 1)
    dr, dc = np.meshgrid(off, off, indexing="ij")
    tree_mean, ncell = [], []
    for x, y in zip(g.x, g.y):
        col0 = int((x - tr.c) // res)
        row0 = int((y - tr.f) // tr.e)
        rr, cc = row0 + dr.ravel(), col0 + dc.ravel()
        keep = (rr >= 0) & (rr < h) & (cc >= 0) & (cc < w)
        rr, cc = rr[keep], cc[keep]
        cx = tr.c + (cc + 0.5) * res
        cy = tr.f + (rr + 0.5) * tr.e
        near = (cx - x) ** 2 + (cy - y) ** 2 <= TREE_RADIUS_M ** 2
        v = L.tree[rr[near], cc[near]]
        v = v[np.isfinite(v)]
        tree_mean.append(100 * v.mean() if v.size else np.nan)
        ncell.append(v.size)
    s["tree_pct_200m"] = np.round(tree_mean, 1)
    s["n_cells_200m"] = ncell
    s["hotter_half"] = s.diff_from_county_median_c > 0
    s["coolest_fifth"] = s.lst_100m_median_c < q[0]
    s[["school_id", "name", "level", "ward_name", "lst_100m_median_c", "on_hottest_fifth", "hotter_half",
       "coolest_fifth", "tree_pct_200m", "n_cells_200m"]].to_csv(TABLES / "schools_trees_200m.csv", index=False)

    def grp(df: pd.DataFrame) -> dict:
        return dict(n_schools=int(len(df)), median_tree_pct=r1(df.tree_pct_200m.median()),
                    mean_tree_pct=r1(df.tree_pct_200m.mean()),
                    share_under_10pct_trees=r1(100 * (df.tree_pct_200m < 10).mean()))
    trees = dict(radius_m=TREE_RADIUS_M, source="ESA WorldCover 2021 tree fraction on the 30 m grid",
                 hotter_half=grp(s[s.hotter_half]), cooler_half=grp(s[~s.hotter_half]),
                 hottest_fifth=grp(s[s.on_hottest_fifth]), coolest_fifth=grp(s[s.coolest_fifth]),
                 all_schools=grp(s))
    chk["schools_hotter_half_pct"] = r1(100 * s.hotter_half.mean())

    # schools by heat fifth (same thresholds as the land), with tree cover around them
    s["fifth"] = np.digitize(s.lst_100m_median_c, q)
    # schools_heat.csv rounds temperatures to 0.01 degC, which moves two schools across the 80th percentile;
    # use its own on_hottest_fifth flag so the count stays the published 567 (extra.schools)
    s.loc[s.on_hottest_fifth, "fifth"] = 4
    s.loc[~s.on_hottest_fifth & (s.fifth == 4), "fifth"] = 3
    sf = []
    for i, f in enumerate(FIFTHS):
        d = s[s.fifth == i]
        sf.append(dict(group=f, n_schools=int(len(d)), share_pct=r1(100 * len(d) / len(s)),
                       median_tree_pct=r1(d.tree_pct_200m.median()), share_under_10pct_trees=r1(100 * (d.tree_pct_200m < 10).mean())))
    trees["fifths"] = sf
    chk["schools_hottest_fifth_n_matches"] = bool(sf[4]["n_schools"] == int(s.on_hottest_fifth.sum()))

    # schools by ward
    bw = (s.groupby("ward_name").agg(schools=("school_id", "size"), on_hottest_fifth=("on_hottest_fifth", "sum"),
                                     on_hotter_half=("hotter_half", "sum"), median_school_lst_c=("lst_100m_median_c", "median"),
                                     median_tree_pct_200m=("tree_pct_200m", "median")).reset_index())
    bw["median_school_lst_c"] = bw.median_school_lst_c.round(1)
    bw["median_tree_pct_200m"] = bw.median_tree_pct_200m.round(1)
    trees["by_ward"] = {r.ward_name: dict(schools=int(r.schools), on_hottest_fifth=int(r.on_hottest_fifth),
                                          median_school_lst_c=r1(r.median_school_lst_c), median_tree_pct_200m=r1(r.median_tree_pct_200m))
                        for r in bw.itertuples() if r.ward_name in ("Kangemi", "Viwandani", "Karen", "Baba Dogo", "Kitisuru")}

    # ---------- results
    def side(name: str) -> dict:
        r = t.loc[name]
        d = dict(people=k(r.people), people_share_pct=r1(r.people_share_of_county_pct))
        for b in BANDS:
            d[b] = k(r[b])
            d[b + "_share_pct"] = r1(r[b + "_share_of_county_pct"])
        d["school_going_4_17"] = k(r["school_age_4_17_school_going"])
        d["school_age_4_17_scaled_to_census"] = k(r["school_age_4_17_scaled"])
        d["children_4_17_per_100_people"] = r1(r.children_4_17_per_100_people)
        return d

    results = dict(
        generated=now_local(),
        method_note=("Children estimated by splitting WorldPop 2025 people in each 30 m cell with the 2019 census "
                     "age mix of the cell's census sub-county; estimates, not counts."),
        census_commit=CENSUS_COMMIT,
        thresholds_c=dict(p20=r1(q[0]), p40=r1(q[1]), median=r1(med), p60=r1(q[2]), p80=r1(q[3])),
        attendance_rates_pct=dict(age_4_5=r1(100 * att[4]), age_6_13=r1(100 * att[6]), age_14_17=r1(100 * att[14])),
        sides={g: side(g) for g in FIFTHS + ["hotter half", "cooler half", "county"]},
        checks=chk,
    )
    people_by_heat = dict(
        fifths=[dict(group=f, people=k(t.loc[f, "people"]), share_pct=r1(t.loc[f, "people_share_of_county_pct"]),
                     land_share_pct=r1(t.loc[f, "land_share_pct"])) for f in FIFTHS],
        hotter_half=dict(people=k(t.loc["hotter half", "people"]), share_pct=r1(t.loc["hotter half", "people_share_of_county_pct"])),
        cooler_half=dict(people=k(t.loc["cooler half", "people"]), share_pct=r1(t.loc["cooler half", "people_share_of_county_pct"])),
        county_people=k(pop_county), thresholds_c=results["thresholds_c"],
    )
    roofs = pd.read_csv(ROOFS)
    nr = roofs[(roofs.county == "NAIROBI CITY") & (roofs.breakdown == "all")]
    results["context"] = dict(
        iron_sheet_households_pct=r1(nr[nr.level == "county"].iron_sheets_pct.iloc[0]),
        iron_sheet_min_subcounty=nr[nr.level == "subcounty"].sort_values("iron_sheets_pct").iloc[0][["name", "iron_sheets_pct"]].tolist(),
        iron_sheet_max_subcounty=nr[nr.level == "subcounty"].sort_values("iron_sheets_pct").iloc[-1][["name", "iron_sheets_pct"]].tolist(),
        adults_hotter_half_share_pct=r1(t.loc["hotter half", "adults_18_plus_share_of_county_pct"]),
        children_hotter_half_scaled_share_pct=r1(100 * t.loc["hotter half", "school_age_4_17_scaled"] / t.loc["county", "school_age_4_17_scaled"]),
        adults_hotter_half_scaled_share_pct=r1(100 * t.loc["hotter half", "adults_18_plus_scaled"] / t.loc["county", "adults_18_plus_scaled"]),
    )

    # ---------- small files for the site's charts and explorer
    lo = [None] + [r1(v) for v in q]
    hi = [r1(v) for v in q] + [None]
    pd.DataFrame([dict(group=f, from_c=lo[i], to_c=hi[i], people=k(t.loc[f, "people"]),
                       share_pct=r1(t.loc[f, "people_share_of_county_pct"])) for i, f in enumerate(FIFTHS)]
                 ).to_csv(SITE_DATA / "people_by_heat.csv", index=False)
    lv = [("pre_primary_4_5", "Pre-primary", "4 to 5"), ("primary_6_11", "Primary", "6 to 11"),
          ("junior_school_12_14", "Junior school", "12 to 14"), ("senior_school_15_17", "Senior school", "15 to 17"),
          ("school_age_4_17", "All school ages", "4 to 17"), ("adults_18_plus", "Adults", "18 and over")]
    pd.DataFrame([dict(key=b, level=n, ages=a, hotter_half=k(t.loc["hotter half", b]), cooler_half=k(t.loc["cooler half", b]),
                       hotter_half_share_pct=r1(t.loc["hotter half", b + "_share_of_county_pct"])) for b, n, a in lv]
                 ).to_csv(SITE_DATA / "children_by_level.csv", index=False)
    pd.DataFrame([dict(**d, from_c=lo[i], to_c=hi[i]) for i, d in enumerate(sf)]).to_csv(SITE_DATA / "schools_by_heat.csv", index=False)
    cw = pd.read_csv(TABLES / "children_by_ward.csv").merge(bw, on="ward_name", how="left")
    cw[["schools", "on_hottest_fifth", "on_hotter_half"]] = cw[["schools", "on_hottest_fifth", "on_hotter_half"]].fillna(0).astype(int)
    cw.to_csv(SITE_DATA / "children_by_ward.csv", index=False)
    results["checks"] = chk

    STANDALONE.write_text(json.dumps(dict(children_by_heat=results, people_by_heat=people_by_heat,
                                          schools_trees_200m=trees), indent=2))
    extra = json.loads(EXTRA.read_text())
    extra["people_by_heat"] = people_by_heat
    extra["children_by_heat"] = results
    extra["schools_trees_200m"] = trees
    EXTRA.write_text(json.dumps(extra, indent=2))
    log.info("written %s", STANDALONE)
    return dict(results=results, people=people_by_heat, trees=trees)


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
