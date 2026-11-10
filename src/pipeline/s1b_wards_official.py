"""Step 1b (v2): replace the geoBoundaries wards with IEBC-based ward boundaries.

Primary source: "Administrative Wards in Kenya 1450" (American Red Cross, HDX, CC BY), the 1,450 IEBC
county assembly wards with topology cleaned and DHIS2 ids. Cross-check: Mikel Maron's
"kenya-election-data" ward layer, built from IEBC 2013 election data.

Writes data/processed/nairobi_wards.geojson (same columns as before, plus subcounty), keeps the old
layer in data/processed/_old/, and writes the validation checks into analysis/checks.json under
"ward_boundaries".

Run: uv run python -m src.pipeline.s1b_wards_official
"""
from __future__ import annotations

import json
import re
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from rasterio.features import rasterize

from src.config import BOUNDARY, PROCESSED, RASTERS, RAW, ROOT, UTM, WARDS, WGS84, get_logger
from src.rasterio_utils import read, read_grid

log = get_logger("s1b_wards_official")

HDX_URL = ("https://data.humdata.org/dataset/e8d06ae7-740b-4491-8749-43f81700cf41/resource/"
           "858129b2-7197-4ffe-b34f-c2091b307b2c/download/kenya_wards.zip")
MARON_URL = "https://raw.githubusercontent.com/mikelmaron/kenya-election-data/master/output/ward.results.zip"
OLD = PROCESSED / "_old" / "nairobi_wards_geoboundaries.geojson"
CHECKS = ROOT / "analysis" / "checks.json"

# The 17 Nairobi constituencies (IEBC, Legal Notice 14 of 2012); sub-counties share the names.
CONSTITUENCIES = {
    "Westlands", "Dagoretti North", "Dagoretti South", "Langata", "Kibra", "Roysambu", "Kasarani",
    "Ruaraka", "Embakasi South", "Embakasi North", "Embakasi Central", "Embakasi East",
    "Embakasi West", "Makadara", "Kamukunji", "Starehe", "Mathare",
}
KIBRA = ["Laini Saba", "Lindi", "Makina", "Woodley/Kenyatta Golf Course", "Sarang'ombe"]
# Source spellings that differ from the IEBC gazette spelling.
FIX = {"Ngara Ward": "Ngara", "Babandogo": "Baba Dogo", "Lower Savanna": "Lower Savannah",
       "Upper Savanna": "Upper Savannah"}


def _download(url: str, folder: str) -> None:
    d = RAW / folder
    d.mkdir(parents=True, exist_ok=True)
    z = d / url.rsplit("/", 1)[-1]
    if not z.exists():
        r = requests.get(url, timeout=600)
        r.raise_for_status()
        z.write_bytes(r.content)
    with zipfile.ZipFile(z) as f:
        f.extractall(d)


def _title(s: str) -> str:
    """Title-case words split by spaces and slashes only, keeping roman numerals and Sarang'ombe."""
    def word(w: str) -> str:
        if re.fullmatch(r"(?i)i{1,3}|iv", w):
            return w.upper()
        return w[:1].upper() + w[1:].lower()
    return re.sub(r"[^ /]+", lambda m: word(m.group(0)), s)


def _clean(name: str) -> str:
    n = re.sub(r"\s+Ward$", "", name.strip())
    n = _title(n)
    return FIX.get(n, n)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower())


def main() -> None:
    _download(HDX_URL, "wards_hdx")
    _download(MARON_URL, "wards_maron")
    hdx = gpd.read_file(RAW / "wards_hdx" / "Kenya_Wards" / "kenya_wards.shp")
    hdx = hdx[hdx["county"] == "Nairobi"].copy()
    hdx["ward_name"] = hdx["ward"].map(_clean)
    hdx["subcounty"] = hdx["subcounty"].str.replace(r"\s+Sub County$", "", regex=True).str.strip()
    hdx = hdx.to_crs(UTM)

    county = gpd.read_file(BOUNDARY).to_crs(UTM)
    cgeom = county.union_all()
    union = hdx.union_all()
    checks: dict = {}
    checks["n_wards"] = int(len(hdx))
    checks["n_wards_ok"] = bool(len(hdx) == 85)
    checks["n_subcounties"] = int(hdx["subcounty"].nunique())
    checks["subcounties_match_iebc"] = bool(set(hdx["subcounty"]) == CONSTITUENCIES)

    # Names against the IEBC election layer (Maron), which lists 84 Nairobi wards.
    maron = gpd.read_file(RAW / "wards_maron" / "ward.results.formatted.shp")
    maron = maron[maron["COUNTY_NAM"] == "NAIROBI"].to_crs(UTM)
    mnames = {_norm(n) for n in maron["NAME"]}
    alias = {"mugumoini": "mugumuini"}   # Maron's spelling of Mugumo-ini
    missing = sorted(n for n in hdx["ward_name"] if alias.get(_norm(n), _norm(n)) not in mnames)
    checks["names_not_in_iebc_election_layer"] = missing
    # Geometry agreement with the election layer: share of each ward's area inside the same-named ward.
    m_by = {alias.get(_norm(n), _norm(n)): g for n, g in zip(maron["NAME"].map(_norm), maron.geometry)}
    agree = []
    for n, g in zip(hdx["ward_name"], hdx.geometry):
        k = alias.get(_norm(n), _norm(n))
        if k in m_by:
            agree.append(g.intersection(m_by[k]).area / g.area)
    checks["median_area_overlap_with_iebc_election_layer_pct"] = round(100 * float(np.median(agree)), 1)
    checks["min_area_overlap_with_iebc_election_layer_pct"] = round(100 * float(np.min(agree)), 1)

    # Union against the county boundary (geoBoundaries ADM1).
    sym = union.symmetric_difference(cgeom).area
    checks["county_area_km2"] = round(cgeom.area / 1e6, 1)
    checks["ward_union_area_km2"] = round(union.area / 1e6, 1)
    checks["symmetric_difference_pct_of_county"] = round(100 * sym / cgeom.area, 2)
    checks["union_matches_county_ok"] = bool(sym / cgeom.area < 0.05)

    # Clip to the county outline so ward edges match the boundary used by every raster.
    w = gpd.clip(hdx, cgeom)
    w = w[w.area > 1000].copy()
    w = w.sort_values("ward_name").reset_index(drop=True)
    w["ward_id"] = [f"NBO-{i + 1:03d}" for i in range(len(w))]
    w["area_km2"] = (w.area / 1e6).round(3)
    w["shapeID"] = w["uid"]
    w["pop2009_census"] = w["pop2009"].round().astype("Int64")

    # Population per ward from WorldPop 2025 on the 30 m grid (same method as the analysis).
    t, width, height = read_grid()
    pop = np.nan_to_num(read(RASTERS / "population_30m.tif"), nan=0.0)

    def ward_pop(gdf: gpd.GeoDataFrame) -> np.ndarray:
        idx = rasterize(((g, i + 1) for i, g in enumerate(gdf.geometry)), out_shape=(height, width),
                        transform=t, fill=0, dtype="int32")
        return np.bincount(idx.ravel(), weights=pop.ravel(), minlength=len(gdf) + 1)[1:]

    w["pop_worldpop2025"] = ward_pop(w).round()
    kib = w[w["ward_name"].isin(KIBRA)].set_index("ward_name")
    checks["kibra_wards"] = {n: dict(area_km2=float(kib.loc[n, "area_km2"]),
                                     pop_worldpop2025=int(kib.loc[n, "pop_worldpop2025"]),
                                     pop2009_census=int(kib.loc[n, "pop2009_census"])) for n in KIBRA}
    checks["kibra_total_worldpop2025"] = int(kib["pop_worldpop2025"].sum())
    checks["kibra_total_census2009"] = int(kib["pop2009_census"].sum())

    # Sanity rules from the v2 brief.
    sc_tot = w.groupby("subcounty")["pop_worldpop2025"].transform("sum")
    w["share_of_subcounty_pct"] = 100 * w["pop_worldpop2025"] / sc_tot
    dens = w["pop_worldpop2025"] / w["area_km2"]
    small_dense = w[(w["area_km2"] < 1) & (dens > 20000) & (w["pop_worldpop2025"] < 10000)]
    dominant = w[w["share_of_subcounty_pct"] > 60]
    checks["rule_small_dense_under_10000"] = small_dense[["ward_name", "area_km2", "pop_worldpop2025"]] \
        .to_dict("records")
    checks["rule_over_60pct_of_subcounty"] = dominant[["ward_name", "subcounty", "share_of_subcounty_pct"]] \
        .round(1).to_dict("records")
    # Also under 1 km2 with fewer than 10,000 people regardless of density, for the record.
    checks["all_under_1km2_with_under_10000"] = w[(w["area_km2"] < 1) & (w["pop_worldpop2025"] < 10000)][
        ["ward_name", "area_km2", "pop_worldpop2025", "pop2009_census"]].to_dict("records")

    # Old vs new: ten most changed wards by WorldPop population.
    old = gpd.read_file(OLD).to_crs(UTM)
    old["pop_old"] = ward_pop(old).round()
    old["k"] = old["ward_name"].map(_norm)
    w["k"] = w["ward_name"].map(_norm)
    old_alias = {"sarangombe": "sarangombe", "babadogo": "babadogo"}
    cmp = w[["k", "ward_name", "subcounty", "area_km2", "pop_worldpop2025"]].merge(
        old[["k", "ward_name", "area_km2", "pop_old"]].rename(columns={"ward_name": "old_name", "area_km2": "old_area_km2"}),
        on="k", how="outer")
    cmp["pop_change"] = cmp["pop_worldpop2025"] - cmp["pop_old"]
    cmp["abs_change"] = cmp["pop_change"].abs()
    top = cmp.sort_values("abs_change", ascending=False).head(10)
    out = top[["ward_name", "subcounty", "old_area_km2", "area_km2", "pop_old", "pop_worldpop2025", "pop_change"]] \
        .rename(columns={"area_km2": "new_area_km2", "pop_old": "pop_old_wards", "pop_worldpop2025": "pop_new_wards"})
    (ROOT / "analysis" / "tables").mkdir(exist_ok=True)
    out.to_csv(ROOT / "analysis" / "tables" / "ward_boundary_change.csv", index=False)
    checks["unmatched_names_old_vs_new"] = sorted(set(cmp.loc[cmp["ward_name"].isna(), "old_name"].dropna())
                                                  | set(cmp.loc[cmp["old_name"].isna(), "ward_name"].dropna()))

    w = w[["ward_id", "ward_name", "subcounty", "shapeID", "area_km2", "pop2009_census", "geometry"]].to_crs(WGS84)
    w.to_file(WARDS, driver="GeoJSON")
    log.info("Saved %d IEBC-based wards to %s", len(w), WARDS)

    allc = json.loads(CHECKS.read_text()) if CHECKS.exists() else {}
    checks["source"] = "Administrative Wards in Kenya 1450, American Red Cross via HDX (CC BY); cross-checked " \
                       "against mikelmaron/kenya-election-data (IEBC 2013)"
    allc["ward_boundaries"] = checks
    CHECKS.write_text(json.dumps(allc, indent=2, default=float))
    log.info("Checks: %s", json.dumps({k: v for k, v in checks.items() if not isinstance(v, (list, dict))}))
    print(json.dumps(checks, indent=1, default=float))
    print(out.to_string())


if __name__ == "__main__":
    main()
