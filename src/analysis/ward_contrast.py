"""People in the five hottest and five coolest wards from the 2019 census (D61).

The "Five hot wards, five cool wards" map step shows how small the hottest wards are and how large the coolest
are. WorldPop gets the people in several of these wards badly wrong (Kangemi about 11,500 against 62,831 in the
census sub-location that matches it), so this step uses the 2019 census instead.

Each ward is matched to the census sub-locations (KNBS 2019 Volume II, table 2.4, in
Kinjuriu/kenya-2019-census-csv at commit d05f526) whose names and combined land area match it. The match is
checked by area: the census land area of the matched units and the ward's area from the IEBC boundary layer.
Kangemi ward is the Kangemi Central sub-location (Gichagi and Mt View make up Mountain View ward, 3.1 km²
against 3.0 km²); Karura ward is the Karura and Muthaiga sub-locations (Highridge, Spring Valley and Upper
Parklands make up Parklands/Highridge, 8.2 km² against 8.8 km²); Karen ward is Karen division (Karen, Lenana,
Hardy and Lang'ata sub-locations, 71.5 km² against 71.2 km²). Baba Dogo and Kabiro wards are larger than their
sub-locations (2.3 against 1.1 km², 1.1 against 0.8 km²); their people come from the sub-location of the same
name, so their density may be slightly understated when divided by the ward's area.

People per km² divide the census population by the ward's area (the shape on the map).

Run: uv run python -m src.analysis.ward_contrast
"""
from __future__ import annotations

import json

import geopandas as gpd
import pandas as pd

from src.config import ROOT, get_logger

log = get_logger("ward_contrast")
SUB = ROOT / "data" / "raw" / "census_2019" / "kenya_2019_census_population_by_sublocation.csv"
WARDS = ROOT / "site" / "public" / "data" / "wards.geojson"
EXTRA = ROOT / "analysis" / "results_extra.json"
TABLE = ROOT / "analysis" / "tables" / "ward_contrast_census.csv"
SITE = ROOT / "site" / "public" / "data" / "ward_contrast.csv"

# ward -> census sub-locations (exact names in the census table, Nairobi City only)
MATCH = {
    "Kangemi": ["KANGEMI CENTRAL"],
    "Viwandani": ["VIWANDANI"],
    "Kabiro": ["KABIRO"],
    "Dandora Area I": ["DANDORA I"],
    "Baba Dogo": ["BABA DOGO"],
    "Kileleshwa": ["KILELESHWA", "MUTHANGARI"],
    "Mutu-ini": ["GITIBA", "MUTUINI"],
    "Karura": ["KARURA", "MUTHAIGA"],
    "Kitisuru": ["KITISURU", "KYUNA", "LORESHO"],
    "Karen": ["KAREN", "LENANA", "HARDY", "LANG'ATA"],
}


def main() -> dict:
    extra = json.loads(EXTRA.read_text())
    hot, cool = extra["wards_top5"]["hot"], extra["wards_top5"]["cool"]
    sub = pd.read_csv(SUB)
    sub = sub[sub.county == "NAIROBI CITY"]
    w = gpd.read_file(WARDS)[["ward_name", "area_km2", "pop_total"]].set_index("ward_name")
    rows = []
    for ward, names in MATCH.items():
        d = sub[sub.name.isin(names)]
        assert len(d) == len(names), (ward, names, d.name.tolist())
        pop = int(d.total.sum())
        rows.append(dict(ward_name=ward, group="hot" if ward in hot else "cool", census_2019=pop,
                         census_land_km2=round(float(d.land_area_km2.sum()), 1), ward_km2=round(float(w.loc[ward, "area_km2"]), 2),
                         people_per_km2=int(round(pop / w.loc[ward, "area_km2"], -2)), worldpop_2025=int(round(w.loc[ward, "pop_total"], -2)),
                         sublocations="; ".join(n.title().replace("'A", "'a") for n in names)))
    t = pd.DataFrame(rows)
    assert set(t.ward_name) == set(hot) | set(cool)
    t.to_csv(TABLE, index=False)
    t[["ward_name", "group", "census_2019", "ward_km2", "people_per_km2"]].to_csv(SITE, index=False)

    def grp(g):
        d = t[t.group == g]
        return dict(people=int(d.census_2019.sum()), people_rounded=int(round(d.census_2019.sum(), -3)),
                    km2=round(float(d.ward_km2.sum()), 1), people_per_km2=int(round(d.census_2019.sum() / d.ward_km2.sum(), -2)),
                    worldpop_2025=int(round(d.worldpop_2025.sum(), -3)))
    res = dict(source="KNBS 2019 census, Volume II table 2.4, sub-locations matched to wards by name and land area (D61)",
               hot=grp("hot"), cool=grp("cool"),
               wards={r.ward_name: dict(census_2019=int(r.census_2019), km2=float(r.ward_km2), people_per_km2=int(r.people_per_km2))
                      for r in t.itertuples()})
    res["density_ratio"] = round(res["hot"]["people_per_km2"] / res["cool"]["people_per_km2"], 1)
    res["area_ratio"] = round(res["cool"]["km2"] / res["hot"]["km2"], 1)
    res["max_area_mismatch_pct"] = round(float((100 * (t.census_land_km2 - t.ward_km2).abs() / t.ward_km2).max()), 1)
    extra["wards_top5_census"] = res
    EXTRA.write_text(json.dumps(extra, indent=2))
    log.info("hot %s cool %s", res["hot"], res["cool"])
    return res


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
