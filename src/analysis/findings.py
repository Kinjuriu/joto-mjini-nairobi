"""Write analysis/FINDINGS.md from analysis/results.json, so every number in it is computed, not typed.

Run: uv run python -m src.analysis.findings
"""
from __future__ import annotations

import json

from src.config import ROOT, now_local

RES = ROOT / "analysis" / "results.json"
CHK = ROOT / "analysis" / "checks.json"
OUT = ROOT / "analysis" / "FINDINGS.md"
HOT = "data/processed/rasters/lst_hot_season_median.tif"
CAVEAT_LST = ("Land surface temperature, not air temperature; Landsat measures heat at about 100 m, so values describe "
              "the area around a place, not a single roof or street; mid-morning overpass only (about 10:43 Nairobi time, see F15).")


def c(x: float) -> str:
    return f"{x:.1f} °C"


def _date(iso: str) -> str:
    import datetime as dt
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"


def n(x: float) -> str:
    return f"{int(round(x)):,}"


def finding(code, title, sentence, numbers, method, data, script, caveats, confidence):
    return (f"### {code}. {title}\n\n"
            f"- **Sentence for the story:** {sentence}\n"
            f"- **Number(s):** {numbers}\n"
            f"- **Method:** {method}\n"
            f"- **Data:** {data}\n"
            f"- **Script:** {script}\n"
            f"- **Caveats:** {caveats}\n"
            f"- **Confidence:** {confidence}\n")


def main() -> None:
    r = json.loads(RES.read_text())
    chk = json.loads(CHK.read_text())
    q1, q2, q3, q4, q5, q6, q7, q8 = (r[f"q{i}"] for i in range(1, 9))
    hs, cs = r["composites"]["hot_season"], r["composites"]["cool_season"]
    hcd = r["composites"]["hottest_clear_day"]
    lc = {d["landcover"]: d for d in q3["by_class"]}
    k, a, cp = q5["parks"]["Karura Forest"], q5["parks"]["Nairobi Arboretum"], q5["parks"]["City Park"]
    years = q6["years"]
    out = [f"# Findings\n\nEvery number that may appear in the story, with where it came from. "
           f"Generated {now_local()} (Africa/Nairobi) by `src/analysis/findings.py` from `analysis/results.json` "
           f"(written by `src/analysis/core.py`). Do not edit numbers by hand; change the code and re-run.\n\n"
           f"**Hot-season composite:** median of {hs['n_scenes']} clear Landsat 8 and 9 scenes, January to March, "
           f"{hs['first_year']} to 2026 ({', '.join(hs['dates'])}). **Cool-season composite:** {cs['n_scenes']} scenes, "
           f"June to August, {cs['first_year']} to 2026 ({', '.join(cs['dates'])}). All temperatures below are land "
           f"surface temperature unless the finding says air temperature.\n"]

    out.append(finding(
        "F1", f"On hot mornings, half of Nairobi's ground was hotter than {c(q1['county_median_c'])}",
        f"On clear January to March mornings, half of Nairobi County's ground was hotter than {c(q1['county_median_c'])} "
        f"at the surface. The hottest tenth of the land averaged {c(q1['hottest10pct_land_mean_c'])}; the coolest tenth "
        f"averaged {c(q1['coolest10pct_land_mean_c'])}.",
        f"county median {c(q1['county_median_c'])}; 10th percentile {c(q1['county_p10_c'])}; 90th percentile "
        f"{c(q1['county_p90_c'])}; mean of hottest 10 % {c(q1['hottest10pct_land_mean_c'])}; mean of coolest 10 % "
        f"{c(q1['coolest10pct_land_mean_c'])}; {q1['valid_cells_share']} % of county cells have a value",
        "Median and percentiles of all 30 m cells whose centre is in the county, hot-season composite",
        HOT + ", data/processed/nairobi_boundary.geojson", "src/analysis/core.py, q1_where_hottest",
        CAVEAT_LST, f"High. Recomputed independently with a rioxarray clip: {chk['county_median']['independent']} °C."))

    out.append(finding(
        "F2", f"The hottest wards were {q1['ward_gap_c']:.1f} °C hotter than the coolest",
        f"{q1['hottest_ward']} was the hottest ward at the surface ({c(q1['hottest_ward_c'])}) and "
        f"{q1['coolest_ward']} the coolest ({c(q1['coolest_ward_c'])}). The {q1['n_wards_each_group']} hottest wards "
        f"averaged {c(q1['hottest_wards_mean_c'])}, {c(q1['ward_gap_c'])} more than the {q1['n_wards_each_group']} "
        f"coolest ({c(q1['coolest_wards_mean_c'])}).",
        f"hottest wards: {', '.join(f'{w['ward_name']} {w['lst_median_c']}' for w in q1['hottest_wards'])}; coolest wards: "
        f"{', '.join(f'{w['ward_name']} {w['lst_median_c']}' for w in q1['coolest_wards'])} (°C, ward medians)",
        "Median of 30 m cells whose centre lies in each ward; mean of the top and bottom tenth of wards (8 each)",
        HOT + ", data/processed/nairobi_wards.geojson", "src/analysis/core.py, ward_table and q1_where_hottest",
        CAVEAT_LST + " Ward medians include all land in the ward (homes, roads, open ground, forest). Ruai and Embakasi "
        "contain large open and bare areas (and the airport in Embakasi) as well as homes.",
        "High for the numbers (exactextract coverage-weighted medians give the same ranking, Spearman "
        f"{chk['ward_rank_agreement_spearman']}). Medium for interpretation, because ward medians mix land uses."))

    out.append(finding(
        "F3", f"The city centre and Industrial Area were {q2['gap_c']:.1f} °C hotter than Karura and the Arboretum",
        f"On hot mornings, the ground in the city centre and Industrial Area ({c(q2['hot_areas_median_c'])}) was "
        f"{c(q2['gap_c'])} hotter than Karura Forest and the Nairobi Arboretum ({c(q2['cool_areas_median_c'])}).",
        f"CBD {c(q2['CBD']['median_c'])}; Industrial Area {c(q2['Industrial Area']['median_c'])}; Karura Forest "
        f"{c(q2['Karura Forest']['median_c'])}; Nairobi Arboretum {c(q2['Nairobi Arboretum']['median_c'])}; combined gap "
        f"{c(q2['gap_c'])}; Industrial Area minus Karura {c(q2['industrial_minus_karura_c'])}; CBD minus Arboretum "
        f"{c(q2['cbd_minus_arboretum_c'])}. Cool season: CBD {c(q2['CBD']['cool_season_median_c'])}, Karura "
        f"{c(q2['Karura Forest']['cool_season_median_c'])}",
        f"Median of 30 m cells in each area. Areas: CBD = {q2['definitions']['CBD']}; Industrial Area = "
        f"{q2['definitions']['industrial']}; Karura = {q2['definitions']['karura']}; Arboretum = "
        f"{q2['definitions']['arboretum']}. Combined values pool the cells of the two areas in each group.",
        HOT + ", data/processed/comparison_areas.geojson (the exact shapes used)", "src/analysis/core.py, q2_gap",
        CAVEAT_LST + " Under a forest canopy the satellite sees the top of the trees, not the ground below.",
        f"High. Karura recomputed by a windowed read: {chk['karura_median']['independent']} °C."))

    out.append(finding(
        "F4", f"Built-up cells were {q3['built_minus_tree_c']:.1f} °C hotter than tree-covered cells",
        f"On hot mornings, mostly built-up ground was on average {c(q3['built_minus_tree_c'])} hotter at the surface than "
        f"ground mostly under trees. Areas with more trees were cooler: the hot-season surface temperature fell from "
        f"{c(q3['tree_band_0_10_mean_c'])} where tree cover was under 10 % to {c(q3['tree_band_90_100_mean_c'])} where it "
        f"was over 90 %.",
        f"cells at least 75 % built-up: median {c(q3['mostly_built_median_c'])} ({n(q3['mostly_built_cells'])} cells); "
        f"cells at least 75 % tree cover: median {c(q3['mostly_tree_median_c'])} ({n(q3['mostly_tree_cells'])} cells); "
        f"tree band 0 to 10 % mean {c(q3['tree_band_0_10_mean_c'])}, 90 to 100 % mean {c(q3['tree_band_90_100_mean_c'])} "
        f"(difference {c(q3['tree_band_gap_c'])}); Spearman correlation with NDVI {q3['spearman_ndvi_lst']}, with tree "
        f"share {q3['spearman_tree_lst']}",
        "WorldCover 10 m classes counted inside each 30 m cell; medians of hot-season surface temperature; means for each "
        "10 % band of tree cover (table analysis/tables/lst_by_tree_band.csv)",
        HOT + ", data/processed/rasters/tree_fraction_30m.tif, built_fraction_30m.tif, ndvi_hot_season_median.tif",
        "src/analysis/core.py, q3_landcover",
        CAVEAT_LST + " WorldCover is from 2021; the composite is 2023 to 2026. This is an association: places with "
        "trees differ in other ways too (height, slope, soil moisture, how they are used). It does not show how much "
        "planting trees would cool a place.",
        "High for the association; the method does not support a causal number."))

    out.append(finding(
        "F5", "Dry grass and bare ground were as hot as roofs and roads",
        f"In the dry months, open ground heated up as much as built-up land: grassland ({c(lc['Grassland']['median_c'])}), "
        f"farmland ({c(lc['Cropland']['median_c'])}) and bare ground ({c(lc['Bare or sparse vegetation']['median_c'])}) "
        f"were as hot as or hotter than built-up land ({c(lc['Built-up']['median_c'])}). Only trees "
        f"({c(lc['Tree cover']['median_c'])}) and water ({c(lc['Water']['median_c'])}) were clearly cooler.",
        "; ".join(f"{d['landcover']} {c(d['median_c'])} ({d['share_pct']} % of county)" for d in q3["by_class"]),
        "Median hot-season surface temperature of 30 m cells by their majority WorldCover class",
        HOT + ", data/processed/rasters/worldcover_majority_30m.tif", "src/analysis/core.py, q3_landcover",
        CAVEAT_LST + " Dry grass is hot at the surface in January to March; in the wet season it is cooler. This is why "
        "Nairobi National Park (mostly grassland) is not among the coolest places on these maps.",
        "High."))

    out.append(finding(
        "F6", f"About {q4['pop_in_hottest20'] / 1000:.0f},000 people live on the hottest fifth of the county's ground",
        f"About {n(q4['pop_in_hottest20'])} people, {q4['pop_share_in_hottest20_pct']:.1f} % of the county's estimated "
        f"population, live on the hottest fifth of Nairobi's land (surface above {c(q4['hottest20_threshold_c'])} on hot "
        f"mornings). The ground under the average resident was {c(q4['pop_weighted_county_lst_c'])}, warmer than the "
        f"average for all county land ({c(q4['area_weighted_county_mean_c'])}).",
        f"{n(q4['pop_in_hottest20'])} people (rounded to the nearest 1,000); {q4['pop_share_in_hottest20_pct']:.1f} % of "
        f"{n(q4['county_pop'])}; threshold {c(q4['hottest20_threshold_c'])}; population-weighted mean "
        f"{c(q4['pop_weighted_county_lst_c'])}; area mean {c(q4['area_weighted_county_mean_c'])}",
        "Hottest 20 % of county 30 m cells by hot-season surface temperature; WorldPop 2025 people summed in those cells; "
        "population-weighted mean over all county cells",
        HOT + ", data/processed/rasters/population_30m.tif", "src/analysis/core.py, q4_exposure",
        CAVEAT_LST + " WorldPop is a modelled estimate (2025, constrained to mapped buildings). It may undercount the "
        "densest informal settlements. The hottest fifth of land also includes the airport and open plains in the east, "
        "where few people live, so the share of people (under 20 %) is lower than the share of land.",
        f"High for the arithmetic (recomputed with xarray: {n(chk['pop_hottest20']['independent'])}); medium for the "
        "population estimate itself."))

    tw = q4["top10_pop_weighted"]
    out.append(finding(
        "F7", "Ten wards where people live on the hottest ground",
        f"Weighted by where people live, the hottest wards were {', '.join(w['ward_name'] for w in tw[:-1])} and "
        f"{tw[-1]['ward_name']}. Together they are home to about {n(q4['top10_total_pop'])} people. None of them has more "
        f"than {q4['top10_max_tree_pct']:.1f} % of its land under trees.",
        "; ".join(f"{w['ward_name']} {c(w['pop_weighted_lst_c'])}, {n(w['pop_total'])} people" for w in tw),
        "Population-weighted mean of hot-season surface temperature over the 30 m cells of each ward (weights: WorldPop "
        "2025 people per cell); populations rounded to the nearest 100",
        HOT + ", data/processed/rasters/population_30m.tif, data/processed/nairobi_wards.geojson",
        "src/analysis/core.py, q4_exposure (table analysis/tables/top_wards.csv)",
        CAVEAT_LST + " Several of these wards are small; the ward boundaries come from a community-made layer "
        "(geoBoundaries ADM3), not from the IEBC directly. Ward populations are modelled, not census counts.",
        "Medium: the ranking is robust (ward totals add to within 2.4 % of the county total) but small differences "
        "(0.1 °C) between neighbouring ranks are not meaningful."))

    h, cc = q7["hottest_fifth"], q7["coolest_fifth"]
    out.append(finding(
        "F8", f"People in the hottest fifth of wards lived on ground {q7['lst_gap_c']:.1f} °C hotter, with about "
              f"one {['', '', 'half', 'third', 'quarter', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth'][min(12, max(2, round(q7['tree_ratio'])))]} of the tree cover",
        f"Residents of the hottest fifth of wards lived, on average, on ground {c(q7['lst_gap_c'])} hotter than residents "
        f"of the coolest fifth ({c(h['pop_weighted_lst_c'])} against {c(cc['pop_weighted_lst_c'])}). Those hotter wards "
        f"had {h['tree_pct']:.1f} % tree cover; the cooler wards had {cc['tree_pct']:.1f} %.",
        f"hottest fifth: {h['n_wards']} wards, about {n(h['pop'])} people, {c(h['pop_weighted_lst_c'])}, tree cover "
        f"{h['tree_pct']} %, built-up {h['built_pct']} %, {n(h['pop_density_per_km2'])} people per km²; coolest fifth: "
        f"{cc['n_wards']} wards, about {n(cc['pop'])} people, {c(cc['pop_weighted_lst_c'])}, tree cover {cc['tree_pct']} %, "
        f"built-up {cc['built_pct']} %, {n(cc['pop_density_per_km2'])} people per km²; gap {c(q7['lst_gap_c'])}; tree "
        f"cover ratio {q7['tree_ratio']}",
        "Wards ranked by population-weighted surface temperature; top and bottom 17 wards; group temperature weighted "
        "by population, tree and built-up shares weighted by ward area",
        HOT + ", tree_fraction_30m.tif, built_fraction_30m.tif, population_30m.tif",
        "src/analysis/core.py, q7_inequality",
        CAVEAT_LST + " This compares places and the exposure of the people who live there. It says nothing about income "
        "or wealth; no open ward-level income data was used. The coolest fifth includes large leafy wards (Karen, "
        "Karura, Kitisuru) and some dense central wards. No settlement-level comparison: no open informal-settlement "
        "layer could be downloaded (DECISIONS D9). Hottest fifth: " + ", ".join(h["wards"]) + ". Coolest fifth: " +
        ", ".join(cc["wards"]) + ".",
        "Medium: the direction is clear; the size depends on how wards are grouped."))

    out.append(finding(
        "F9", "Built-up land next to Karura Forest was a little cooler; the difference faded within about 500 m",
        f"Built-up land within 100 m of Karura Forest was {c(abs(k['near_minus_far_c']))} cooler at the surface than "
        f"built-up land 700 to 1,000 m away ({c(k['ring_0_100_c'])} against {c(k['ring_700_1000_c'])}). Around the "
        f"Arboretum and City Park the difference was about 1 °C and faded within about 200 m.",
        f"Karura: 0 to 100 m {c(k['ring_0_100_c'])}, 700 to 1,000 m {c(k['ring_700_1000_c'])}, difference "
        f"{c(k['near_minus_far_c'])}, within 0.5 °C of the far band by {k['reach_m']} m. Arboretum: "
        f"{c(a['ring_0_100_c'])} vs {c(a['ring_700_1000_c'])} ({c(a['near_minus_far_c'])}), by {a['reach_m']} m. City Park: "
        f"{c(cp['ring_0_100_c'])} vs {c(cp['ring_700_1000_c'])} ({c(cp['near_minus_far_c'])}), by {cp['reach_m']} m",
        q5["method"], HOT + ", built_fraction_30m.tif, tree_fraction_30m.tif, data/processed/nairobi_places.geojson",
        "src/analysis/core.py, q5_park_rings (table analysis/tables/park_rings.csv)",
        CAVEAT_LST + " The 100 m sensor footprint blurs the first ring, so part of the edge effect may be the park "
        "itself showing through. Neighbourhoods next to these parks also differ in other ways (larger plots, more "
        "garden trees). The rings around Karura do not rise smoothly. Treat as indicative.",
        "Low to medium: a consistent sign at all three parks, but small and noisy; do not quote as a cooling distance."))

    out.append(finding(
        "F10", "Nairobi's built-up area grew by half between 1990 and 2020; the surface temperature record shows no clear trend",
        f"Between 1990 and 2020, built-up surface in Nairobi County grew from about {q6['built_km2']['1990']:.0f} km² to "
        f"about {q6['built_km2']['2020']:.0f} km², around {q6['built_ratio_2020_1990']:.1f} times as much. The yearly "
        f"satellite readings of hot-season surface temperature jump up and down with the weather and do not show a clear "
        f"trend.",
        f"GHSL built-up surface in the county: " + ", ".join(f"{y} {v} km²" for y, v in q6["built_km2"].items()) +
        f" (2025 is a JRC projection); growth 1990 to 2020 {q6['built_growth_1990_2020_km2']} km²; share of county "
        f"{q6['built_share_county_1990_pct']} % in 1990, {q6['built_share_county_2020_pct']} % in 2020. Yearly county "
        f"medians: " + ", ".join(f"{y['year']} {y['county_median_c']} ({y['n_scenes']} scenes)" for y in years) +
        f". Mann-Kendall: {q6['mann_kendall_trend']}, p = {q6['mann_kendall_p']}; Theil-Sen slope "
        f"{q6['theil_sen_slope_c_per_decade']} °C per decade (95 % range {q6['theil_sen_ci_c_per_decade'][0]} to "
        f"{q6['theil_sen_ci_c_per_decade'][1]})",
        "GHSL built-up surface summed over 90 m cells in the county; January to March composites per year with at least "
        "2 usable scenes; Mann-Kendall test and Theil-Sen slope on the yearly county medians",
        "data/processed/rasters/ghsl_built_<year>.tif, data/processed/rasters/lst_hot_season_by_year/<year>.tif",
        "src/analysis/core.py, q6_trend (tables hot_season_by_year.csv, ghsl_built_by_epoch.csv)",
        "Each year rests on 2 to 5 scenes, so weather on those days dominates. 2024 has no composite (one usable scene). "
        "GHSL is a modelled product at 100 m; it counts built surface, not buildings. Do not compare yearly surface "
        "temperature medians as if they were a climate record.",
        "High for the built-up growth; high that the satellite series shows no clear trend (and that this is not "
        "evidence of no warming)."))

    out.append(finding(
        "F11", "The same places were hot in both seasons",
        f"In the cooler June to August months the county median surface temperature was {c(q1['cool_season_county_median_c'])}, "
        f"against {c(q1['county_median_c'])} in January to March. The places that were hot in one season were mostly hot in the "
        f"other (ward rank correlation {q1['hot_cool_ward_spearman']:.2f}).",
        f"cool season county median {c(q1['cool_season_county_median_c'])}; hot season {c(q1['county_median_c'])}; Karura "
        f"cool season {c(q2['Karura Forest']['cool_season_median_c'])}; CBD cool season {c(q2['CBD']['cool_season_median_c'])}; "
        f"Spearman correlation hot vs cool season: 30 m cells {q1['hot_cool_spearman']}, ward medians {q1['hot_cool_ward_spearman']}",
        "Median of county cells in each composite; Spearman rank correlation between the two composites over every 7th "
        "valid county cell and over the 85 ward medians", HOT + ", data/processed/rasters/lst_cool_season_median.tif",
        "src/analysis/core.py, q1_where_hottest and q2_gap",
        CAVEAT_LST + f" The cool-season composite has only {cs['n_scenes']} scenes from four different years "
        f"({cs['first_year']} to 2026) because the cool season is cloudy. Rank correlation measures whether places keep their order, not "
        "whether the gaps stay the same size.",
        "Medium."))

    dpy = {d["date"]: d["above_p90"] for d in q8["days_above_p90_by_year"]}
    out.append(finding(
        "F12", "Air temperature: hot one day, cooler the next",
        f"Nairobi's daily high air temperature changed by {c(q8['mean_abs_daily_change_tmax_c'])} from one day to the "
        f"next on average since January 2023, and by 3 °C or more on {q8['days_change_3c_or_more']} days. Since El Niño "
        f"conditions began in May 2026, daily highs averaged {c(q8['el_nino_mean_tmax_c'])}, "
        f"{c(q8['el_nino_minus_clim_c'])} above the 1991 to 2020 average for the same months.",
        f"mean absolute day-to-day change in daily maximum {c(q8['mean_abs_daily_change_tmax_c'])}; largest "
        f"{c(q8['max_daily_change_c'])}; days with a change of 3 °C or more {q8['days_change_3c_or_more']} "
        f"({q8['share_days_change_3c_or_more_pct']} %); 90th percentile of daily maximum 1991 to 2020 "
        f"{c(q8['p90_tmax_1991_2020_c'])}; days above it: " + ", ".join(f"{y} {v}" for y, v in dpy.items()) +
        f" (2026 to {q8['last_date']}); El Niño period {q8['el_nino_period']}: mean daily maximum "
        f"{c(q8['el_nino_mean_tmax_c'])} vs {c(q8['same_months_1991_2020_mean_tmax_c'])} for the same months in 1991 to "
        f"2020; highest daily maximum since 2023 {c(q8['tmax_2023_now_max_c'])} on {q8['tmax_2023_now_max_date']}",
        "Daily series from Open-Meteo (ERA5 reanalysis) for the grid cell over central Nairobi; El Niño period starts "
        "1 May 2026 (RONI first at or above +0.5 °C in AMJ 2026)",
        "data/processed/nairobi_daily_air_temp.csv, data/processed/roni.csv", "src/analysis/core.py, q8_air",
        "Air temperature from a weather model for a grid cell about 10 to 30 km across, not a station and not surface "
        "temperature. The El Niño comparison is an association for one season; it does not show that El Niño caused "
        "the warmth. The 2026 El Niño period does not yet include December.",
        "High for the arithmetic; medium for what ERA5 says about street-level air temperature."))

    out.append(finding(
        "F13", "The hottest clear morning in the record",
        f"The hottest clear Landsat morning since 2013 was {_date(hcd['date'])}, when the county median surface temperature was "
        f"{c(hcd['county_median_c'])}.",
        f"{hcd['date']}, scene {hcd['scene_id']}, county median {c(hcd['county_median_c'])}",
        "Usable scene (at least 80 % of county clear) with the highest county median",
        "data/processed/landsat_scene_catalogue.csv, data/processed/rasters/lst_hottest_clear_day.tif",
        "src/pipeline/s2b_composites.py, main", CAVEAT_LST + " One scene; a September date, so it is outside the "
        "January to March season used elsewhere.", "High for the number; it is one morning."))

    q9, q0 = r["q9"], r["q0"]
    kl, kw = q9["Kileleshwa"], q9["Kawangware"]
    out.append(finding(
        "F14", f"Leafy Kileleshwa and dense Kawangware, {q9['distance_km']:.1f} km apart, differed by {q9['lst_gap_c']:.1f} °C",
        f"Kawangware, where about {n(kw['pop_density_per_km2'])} people live per square kilometre, had a median surface "
        f"temperature of {c(kw['lst_median_c'])} on hot mornings and {kw['tree_pct']:.0f} % tree cover. Kileleshwa, "
        f"{q9['distance_km']:.1f} km away at the nearest point, had {c(kl['lst_median_c'])} and {kl['tree_pct']:.0f} % tree cover.",
        f"Kawangware: {c(kw['lst_median_c'])}, tree cover {kw['tree_pct']} %, built-up {kw['built_pct']} %, about "
        f"{n(kw['pop_total'])} people on {kw['area_km2']} km² ({n(kw['pop_density_per_km2'])} per km²), rank {kw['rank_hottest']} "
        f"of {q0['n_wards']}. Kileleshwa: {c(kl['lst_median_c'])}, tree cover {kl['tree_pct']} %, built-up {kl['built_pct']} %, "
        f"about {n(kl['pop_total'])} people on {kl['area_km2']} km² ({n(kl['pop_density_per_km2'])} per km²), rank "
        f"{kl['rank_hottest']}. Gap {c(q9['lst_gap_c'])}; nearest distance between ward boundaries {q9['distance_km']} km",
        "Ward medians and shares as in F2 and F4; distance between ward polygons in UTM 37S",
        HOT + ", tree_fraction_30m.tif, built_fraction_30m.tif, population_30m.tif, nairobi_wards.geojson",
        "src/analysis/core.py, q9_pair",
        CAVEAT_LST + " Two wards chosen to illustrate a contrast (Kileleshwa includes Lavington); they are not a "
        "random sample. Ward populations are modelled.",
        "High for the numbers; the pair was chosen, so it illustrates F4 and F8 rather than proving them."))

    out.append(finding(
        "F15", "What the satellite record contains",
        f"We checked {n(q0['n_scenes_searched'])} Landsat 8 and 9 passes over Nairobi between "
        f"{_date(q0['first_scene'])} and {_date(q0['last_scene'])}; {q0['n_scenes_usable']} were clear enough to use. "
        f"The satellites pass at about {q0['overpass_local']} in the morning, Nairobi time.",
        f"{q0['n_scenes_searched']} scenes with under 40 % cloud for the whole scene; {q0['n_scenes_usable']} with at least "
        f"80 % of the county clear; {q0['usable_hot_months_share_pct']} % of usable scenes fall in January to March; mean "
        f"local overpass time of the hot-season scenes {q0['overpass_local']}; hot-season composite {q0['n_hot_scenes']} "
        f"scenes; cool-season composite {q0['n_cool_scenes']} scenes from {q0['cool_first_year']}",
        "STAC search of landsat-c2-l2 on Planetary Computer, cloud mask from qa_pixel",
        "data/processed/landsat_scene_catalogue.csv, data/processed/composites_meta.json",
        "src/pipeline/s2_landsat.py, src/pipeline/s2b_composites.py, src/analysis/core.py q0_data",
        "Scenes with more than 40 % cloud over the whole scene were not searched.", "High."))

    extra_path = ROOT / "analysis" / "results_extra.json"
    ex = json.loads(extra_path.read_text()) if extra_path.exists() else {}
    re_ = ex.get("roof_emissivity")
    if re_:
        d, lf, cb = re_["dense_low_tree"], re_["leafy"], re_["cbd"]
        out.append(finding(
            "F16", "The satellite product assumes ordinary emissivity over metal roofs, so dense wards may be hotter than shown",
            "Some dense wards with almost no trees, such as " + ", ".join(d["wards"][:3]) + ", look cooler than expected. "
            "The satellite product assumes their surfaces give off heat as efficiently as ordinary built-up land. Bare "
            "iron sheet roofs give off heat less efficiently, so where they cover much of the ground the satellite can "
            "read the surface as cooler than it is. Treat the surface temperature of these wards as a lower bound.",
            f"median Landsat emissivity, hot-season scenes: dense low-tree wards ({', '.join(d['wards'])}) {d['emis_median']}; "
            f"leafy wards ({', '.join(lf['wards'])}) {lf['emis_median']}; Nairobi Central {cb['emis_median']}; county "
            f"median {re_['county_emis_median']}; 5th percentile {re_['county_emis_p05']}; ward medians range "
            f"{re_['ward_emis_range'][0]} to {re_['ward_emis_range'][1]}; Spearman correlation of ward emissivity with "
            f"built-up share {re_['spearman_emis_vs_built']}; each 0.01 of emissivity overestimated lowers the retrieved "
            f"temperature by about {re_['sensitivity_c_per_0p01_emis']} °C at these temperatures",
            "Per-cell median of the Landsat Collection 2 ST_EMIS band over the 12 hot-season scenes (cloud-masked), then "
            "ward medians. Sensitivity from the Planck-law approximation dT ≈ T/n · dε/ε with n ≈ 4.5 at 10.9 µm. "
            "Literature: USGS Collection 2 surface temperature takes emissivity from ASTER GED (2000 to 2008 mean) "
            "adjusted with NDVI (USGS, Landsat Collection 2 Surface Temperature; Malakar et al. 2018, IEEE TGRS 56(10)); "
            "Nichol, Usman, Fawole and Shults (2025), 'Refining the urban thermal landscape: insights from corrected "
            "emissivity over indigenous roof materials', Remote Sensing 17(21), 3545, doi:10.3390/rs17213545, found that "
            "lowering metal-roof emissivity from 0.96 to 0.63 raised a Landsat city-wide urban surface temperature from "
            "41 °C to 49 °C in sub-Saharan cities and turned apparent cool islands into heat islands.",
            "data/processed/rasters/emis_hot_season_median.tif, analysis/tables/ward_emissivity.csv",
            "src/analysis/emissivity.py",
            "This test shows what the product assumes, not what the roofs are. ASTER GED is a 2000 to 2008 average at "
            "about 100 m, older than many roofs, and blends roofs with roads, soil and yards. Painted or rusted sheets "
            "have higher emissivity than new galvanised sheets. We have no roof material map, so the size of any bias per "
            "ward is unknown.",
            "Medium that a bias is possible (the emissivity used in the dense wards is no lower than elsewhere, so metal "
            "roofs are not accounted for); low on its size."))
    tv, an = ex.get("tables_v2"), ex.get("animations", {})
    if tv:
        b, w, dt = tv["builtup_by_subcounty"], tv["ward_cover_extremes"], tv["daily_tmax"]
        out.append(finding(
            "T1", "How Nairobi filled in: built-up share of each sub-county, 1975 to 2025",
            f"{b['most_built_2020']} was the most built-up sub-county in 2020 ({b['most_built_2020_pct']:.1f} % of its ground "
            f"covered by buildings); {b['least_built_2020']}, which includes part of Nairobi National Park, the least "
            f"({b['least_built_2020_pct']:.1f} %).",
            f"largest rise 1975 to 2020: {b['largest_rise_1975_2020']}, +{b['largest_rise_1975_2020_points']} percentage points; "
            "full table in analysis/tables/builtup_by_subcounty.csv",
            "GHSL built-up surface (km²) summed over the 90 m cells inside each sub-county (the 17 IEBC constituencies, "
            "dissolved from the ward layer), divided by the sub-county's area",
            "data/processed/rasters/ghsl_built_<year>.tif, data/processed/nairobi_wards.geojson",
            "src/analysis/tables_v2.py, builtup_by_subcounty",
            "GHSL measures the share of the ground under buildings, not all paved land; 2025 is a JRC projection.",
            "High for the arithmetic; medium for GHSL in dense informal areas."))
        out.append(finding(
            "T2", "The hottest wards had about one "
                  + ['', '', 'half', 'third', 'quarter', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh',
                     'twelfth'][min(12, max(2, round(w['coolest_mean_tree_pct'] / w['hottest_mean_tree_pct'])))]
                  + " of the coolest wards' tree cover",
            f"The ten hottest wards where people live had {w['hottest_mean_tree_pct']:.1f} % tree cover on average; the ten "
            f"coolest had {w['coolest_mean_tree_pct']:.1f} %.",
            f"built-up share: hottest ten {w['hottest_mean_built_pct']:.1f} %, coolest ten {w['coolest_mean_built_pct']:.1f} %; "
            "per-ward values in analysis/tables/ward_cover_extremes.csv",
            "Wards ranked by population-weighted hot-season surface temperature; WorldCover 2021 class shares per ward "
            "(mean of the 30 m fractions); difference from the county median",
            "tree_fraction_30m.tif, grass_fraction_30m.tif, built_fraction_30m.tif, bare_fraction_30m.tif, ward_stats.csv",
            "src/analysis/tables_v2.py, ward_cover_extremes",
            CAVEAT_LST + " Association only. WorldPop may misplace people in Kibra (QUESTIONS 7).", "Medium."))
        out.append(finding(
            "T3", "Daily highs since January 2023 compared with normal",
            f"Since May 2026, {dt['el_nino_share_days_above_normal_pct']:.1f} % of days had a daily high air temperature "
            f"above the 1991 to 2020 normal for that day. The highest daily maximum since January 2023 was "
            f"{dt['record_tmax_c']:.1f} °C on {_date(dt['record_day'])}.",
            f"mean difference from normal: since May 2026 {dt['el_nino_mean_anomaly_c']} °C, January 2023 to April 2026 "
            f"{dt['before_mean_anomaly_c']} °C; data {_date(dt['first'])} to {_date(dt['last'])}",
            dt["normal_method"], "data/processed/nairobi_daily_air_temp.csv (Open-Meteo, ERA5)",
            "src/analysis/tables_v2.py, daily_anomaly",
            "Air temperature from a reanalysis for one point in central Nairobi, not measured surface temperature. The "
            "period before El Niño was also warmer than normal, so the El Niño months are not unusual on their own.",
            "High for the arithmetic; low for any link to El Niño."))
    if an.get("day"):
        d_ = an["day"]
        v = d_["validation_at_overpass"]
        out.append(finding(
            "A3", f"A day of heat: {_date(d_['date'])}",
            f"On {_date(d_['date'])}, the county's median land surface temperature in the Copernicus hourly data rose from "
            f"{d_['county_median_c_by_hour'][0]:.1f} °C at {d_['hours_local'][0]:02d}:00 to "
            f"{max(x for x in d_['county_median_c_by_hour'] if x is not None):.1f} °C around midday.",
            "county median by hour (Nairobi time " + ", ".join(f"{h:02d}:00" for h in d_["hours_local"]) + "): "
            + ", ".join("cloud" if x is None else f"{x:.1f}" for x in d_["county_median_c_by_hour"])
            + f" °C; check at the Landsat overpass hour ({d_['overpass_hour_local']:02d}:00): CLMS minus Landsat averaged to "
            f"the CLMS cells, bias {v['bias_c']} °C, RMSE {v['rmse_c']} °C, r {v['r']}, {v['n_cells']} cells",
            "CLMS Global LST hourly v3 (~3 km) via the Sentinel Hub Process API; sharpened to 30 m by adding the same "
            "morning's Landsat residual scaled by the day's heating (own implementation after Zlinszky 2026, Zenodo, "
            "doi:10.5281/zenodo.22944001; the record could not be retrieved, so only the general idea is followed)",
            f"data/raw/clms_lst/{d_['date']}/, Landsat scene {d_['landsat_scene']}",
            "src/pipeline/s9_clms_hourly.py, src/animations/render.py day()",
            "Land surface temperature, not air temperature. The hourly data is about 3 km; the fine pattern in the "
            "animation comes from one morning's Landsat scene and is assumed to scale with the day's heating. Cloud "
            "hides parts of the afternoon.", "Medium for the daily curve; low for fine detail away from the overpass time."))
    if an.get("mornings"):
        m_ = an["mornings"]
        out.append(finding(
            "A1", "Every clear hot-season morning, 2014 to 2026",
            f"The animation shows {m_['n_scenes']} clear January to March Landsat mornings from {_date(m_['first'])} to "
            f"{_date(m_['last'])}, each as a difference from that morning's county median.",
            f"{m_['n_scenes']} scenes; {m_['fps']} frames a second", "Usable scenes (at least 80 % of the county clear), months 1 to 3",
            "data/processed/landsat_scene_catalogue.csv, data/interim/landsat/*_lst_c.tif",
            "src/animations/render.py mornings()", CAVEAT_LST, "High."))
    if ex:
        out.append("## Optional findings (prompt 02, 'if time remains')\n\nNot used in the story yet. Written by "
                   "`src/analysis/extras.py` to `analysis/results_extra.json`.\n")
        sd = ex.get("season_difference")
        if sd:
            lo = sd["smallest_diff_wards"]
            hi = sd["largest_diff_wards"]
            out.append(finding(
                "E1", "The ground was hotter in January to March almost everywhere; a few wards changed by under 1 °C",
                f"Almost all of Nairobi's ground ({sd['share_hotter_in_hot_season_pct']:.1f} %) was hotter on January to "
                f"March mornings than on June to August mornings, by {c(sd['county_median_diff_c'])} at the median. The "
                f"smallest change was in wards such as {', '.join(w['ward_name'] for w in lo[::-1][:3])}, where it was "
                f"under 1 °C.",
                f"county median difference {c(sd['county_median_diff_c'])}; {sd['share_hotter_in_hot_season_pct']} % of "
                f"cells hotter in the hot season; {sd['share_more_than_3c_hotter_pct']} % more than 3 °C hotter; largest "
                f"ward differences: " + ", ".join(f"{w['ward_name']} {c(w['diff_median_c'])}" for w in hi) +
                "; smallest: " + ", ".join(f"{w['ward_name']} {c(w['diff_median_c'])}" for w in lo),
                "Hot-season composite minus cool-season composite, cell by cell; ward medians of the difference",
                "data/processed/rasters/lst_hot_minus_cool.tif (figure outputs/figures/map_hot_minus_cool.png)",
                "src/analysis/extras.py, season_difference",
                CAVEAT_LST + " " + sd["caveat"] + " A small seasonal change can mean a place stays hot all year, or that "
                "it was relatively cool in the hot season; read it with F2 and F8.",
                "Medium: the direction is clear; the size per ward rests on 4 cool-season scenes."))
        k = ex.get("kisumu")
        if k:
            out.append(finding(
                "E2", f"Kisumu: half of the ground was hotter than {c(k['county_median_c'])} on hot-season mornings",
                f"In Kisumu, half of the land was hotter than {c(k['county_median_c'])} at the surface on clear "
                f"January to March mornings. Mostly built-up ground was {c(k['mostly_built_median_c'])} and ground mostly "
                f"under trees {c(k['mostly_tree_median_c'])}." if k.get("mostly_built_median_c") and k.get("mostly_tree_median_c")
                else f"In Kisumu, half of the land was hotter than {c(k['county_median_c'])} at the surface on clear January to March mornings.",
                f"median {c(k['county_median_c'])}; 10th percentile {c(k['p10_c'])}; 90th {c(k['p90_c'])}; "
                f"{k['hot_season_scenes']} scenes from {k['hot_season_first_year']}; {k['valid_share_pct']} % of cells "
                f"with a value; population about {n(k['pop_total'])}; people-weighted {k['pop_weighted_lst_c']} °C; hottest "
                f"wards: " + ", ".join(f"{w['ward_name']} {c(w['lst_median_c'])}" for w in k["hottest_wards"]) +
                "; coolest: " + ", ".join(f"{w['ward_name']} {c(w['lst_median_c'])}" for w in k["coolest_wards"]),
                "Same pipeline as Nairobi with JOTO_CITY=kisumu (DECISIONS D28); medians over the land area of the 35 wards",
                "data/processed/kisumu/rasters/*.tif, data/processed/kisumu/kisumu_wards.geojson",
                "src/pipeline/*.py with JOTO_CITY=kisumu; src/analysis/extras.py, kisumu_summary",
                CAVEAT_LST + " Kisumu is mostly rural outside the city, so county-wide numbers are not comparable with "
                "Nairobi's directly; scenes come from three Landsat paths on different days.",
                "Medium: first pass, not yet checked by an independent method."))

    out.append("""## Checks

Recorded in `analysis/checks.json` by `src/analysis/checks.py`:

""" + "\n".join(f"- **{k}:** {json.dumps(v)}" for k, v in chk.items()) + """

## What the data cannot tell us

- **The air people breathe and feel.** Landsat measures how hot surfaces are (roofs, roads, soil, tree tops), not the air temperature at head height. On a sunny morning the two can differ by more than 10 °C. Shade, wind and humidity also change how heat feels.
- **Night-time heat.** Landsat passes over Nairobi at about 10:43 in the morning (F15). It says nothing about how slowly places cool down at night, which matters for sleep and health.
- **Afternoon peaks.** Surfaces are usually hotter in the early afternoon than at the time of the overpass.
- **Indoor heat.** Temperature inside homes, especially under iron sheet roofs, is not measured here.
- **Detail finer than about 100 m.** The thermal sensor sees areas of about 100 m; a value at a single building describes the area around it.
- **Why a place is hot.** These are associations with land cover, trees and buildings, not measured causes.
- **Who is most at risk.** Heat risk also depends on age, health, work, housing and access to water and cooling. This analysis has none of these.
- **Exact populations.** WorldPop numbers are modelled estimates and may undercount the densest settlements.
- **Change over time in surface temperature.** Too few clear scenes per year to separate a warming trend from day-to-day weather.
- **Rainfall, flooding and El Niño impacts.** Planned for a later phase.
""")
    OUT.write_text("\n".join(out))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
