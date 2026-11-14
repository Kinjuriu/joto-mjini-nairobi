"""School locations for Nairobi County, from every open source we could reach, merged and de-duplicated.

Sources (data/SOURCES.md, "Schools"):
  1. Ministry of Education school list, as published by the World Bank on energydata.info (CC BY 4.0). The
     download links are behind a bot check, so we read the same records from the dataset's public vector tiles
     at zoom 10, which carry every attribute including exact X_Coord / Y_Coord. Each record says whether it
     comes from "Ministry of Education, 2016" or "Open Data Kenya, School 2007".
  2. OpenStreetMap through Overpass (ODbL): amenity=school and amenity=kindergarten, nodes, ways and relations
     (ways and relations as their centre point).
  Checked but not merged: the HOT OpenStreetMap education export on HDX (the same OpenStreetMap features, a few
  days older); Open Schools Kenya on open.africa (an OpenStreetMap extract from 2023); opendata.go.ke primary
  schools 2007 (dead link); UNICEF Giga (API needs a key). Counts are written to data/raw/schools/source_counts.json.

Merge rules. Names are compared after removing generic words (school, primary, academy, ...) with difflib.
  Rule 1: within MERGE_M (50 m) and name similarity at least NAME_SIM (0.75).
  Rule 2: from different sources, name similarity at least FAR_SIM (0.9) and within FAR_M (500 m). Same-name
  matches between the official lists and OpenStreetMap are typically 100 to 500 m apart, so rule 1 alone
  leaves many duplicates.
  Official points are also tried at their Arc 1960 -> WGS84 position, because part of both official lists was
  stored in the old Arc 1960 datum (about 300 m off at Nairobi).
Names must share at least one distinctive word (not "community", "church", "hope", ...). Groups are never joined,
even through a third record, when any pair across them conflicts: levels both known and different; "Old" against
"New"; "Girls" against "Boys"; an "Academy" against a "Primary/Secondary/High" name; an ECD/nursery/kindergarten
against a "Primary/Secondary/High" name; or two records from the same source more than 150 m apart. Pairs are
joined nearest first. Unnamed records are never merged. Location: OpenStreetMap when the school is there (mapped on the ground or from
imagery), otherwise the Ministry point. Ownership: the Ministry's Public/Private when given, otherwise
OpenStreetMap operator:type.

Run: uv run python -m src.pipeline.s10_schools [--fetch]
"""
from __future__ import annotations

import difflib
import glob
import json
import math
import re
import sys

import geopandas as gpd
import mapbox_vector_tile
import numpy as np
import pandas as pd
import requests
from shapely.geometry import Point

from src.config import BOUNDARY, PROCESSED, RAW, SITE_DATA, UTM, WGS84, get_logger
from src.pipeline.s1_boundaries import OVERPASS

log = get_logger("s10_schools")

DIR = RAW / "schools"
MOE_TILES = "https://energydata-tiles-bk.s3.amazonaws.com/tiles/849830e2-fcb5-4b42-8d33-e42c7c1e90b4/10/{x}/{y}.pbf"
MOE_TILE_RANGE = (range(616, 619), range(515, 518))   # zoom 10 tiles covering Nairobi County
OSM_JSON = DIR / "osm_overpass" / "schools_kindergartens.json"
HOT_PARQUET = DIR / "hot_osm" / "education_facilities.parquet"
OSK_CSV = DIR / "open_schools_kenya" / "all-schools-data.csv"
BBOX = (-1.45, 36.65, -1.16, 37.11)   # south, west, north, east
OUT = PROCESSED / "nairobi_schools.geojson"
OUT_SITE = SITE_DATA / "schools.geojson"
MERGE_M = 50.0           # rule 1: within 50 m and names similar (difflib ratio >= NAME_SIM)
NAME_SIM = 0.75
FAR_M = 500.0            # rule 2: different sources, names near-identical (>= FAR_SIM), within 500 m
FAR_SIM = 0.9
SAME_SOURCE_M = 150.0    # two records from one source further apart than this are two schools (e.g. two campuses)
# Arc 1960 to WGS84 at Nairobi, in metres east and north (pyproj EPSG:4210 -> EPSG:4326, measured at 36.82 E,
# 1.29 S). Part of the 2007 and 2016 official lists sits this far from the same school in OpenStreetMap.
ARC1960_DX, ARC1960_DY = 93.0, -286.0
GENERIC = {"SCHOOL", "SCHOOLS", "SCH", "PRIMARY", "PRI", "SECONDARY", "SEC", "HIGH", "ACADEMY", "ACADEMIC",
           "CENTRE", "CENTER", "EDUCATION", "EDUCATIONAL", "THE", "OF", "AND", "ST", "S", "NURSERY", "ECDE", "ECD",
           "KINDERGARTEN", "PRE", "PREPARATORY", "JUNIOR", "MIXED", "DAY", "BOARDING", "COMPLEX", "LTD"}
LEVELS = ["pre-primary", "primary", "secondary"]


# ---------------------------------------------------------------- fetch

def fetch() -> None:
    (DIR / "moe_worldbank").mkdir(parents=True, exist_ok=True)
    for x in MOE_TILE_RANGE[0]:
        for y in MOE_TILE_RANGE[1]:
            r = requests.get(MOE_TILES.format(x=x, y=y), timeout=60)
            r.raise_for_status()
            (DIR / "moe_worldbank" / f"tile_10_{x}_{y}.pbf").write_bytes(r.content)
    q = (f'[out:json][timeout:240];(nwr["amenity"~"^(school|kindergarten)$"]({",".join(map(str, BBOX))}););'
         'out center tags;')
    OSM_JSON.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        r = requests.post(OVERPASS, data={"data": q}, timeout=300,
                          headers={"User-Agent": "joto-mjini-nairobi research"})
        if r.ok and r.text.lstrip().startswith("{"):
            OSM_JSON.write_text(r.text)
            return
        log.warning("Overpass attempt %d failed: HTTP %s", attempt + 1, r.status_code)
    raise RuntimeError("Overpass failed three times")


# ---------------------------------------------------------------- read sources

def level_from_name(name: str) -> str | None:
    n = name.upper()
    if re.search(r"\b(NURSERY|KINDERGARTEN|ECDE?|PRE[- ]?SCHOOL|PRE[- ]?PRIMARY|DAY ?CARE|BABY ?CARE)\b", n):
        return "pre-primary"
    if re.search(r"\b(PRIMARY|PRI)\b", n):
        return "primary"
    if re.search(r"\b(SECONDARY|SEC|HIGH SCHOOL|GIRLS HIGH|BOYS HIGH)\b", n):
        return "secondary"
    if re.search(r"\b(ADULT|VOCATIONAL|POLYTECHNIC|COLLEGE|UNIVERSITY|INSTITUTE|TRAINING)\b", n):
        return "other"
    return None


def read_moe() -> gpd.GeoDataFrame:
    recs, seen = [], set()
    for f in sorted(glob.glob(str(DIR / "moe_worldbank" / "tile_10_*.pbf"))):
        layer = mapbox_vector_tile.decode(open(f, "rb").read()).get("data_layer", {})
        for feat in layer.get("features", []):
            p = feat["properties"]
            if p.get("OBJECTID") in seen or not str(p.get("County", "")).upper().startswith("NAIROBI"):
                continue
            seen.add(p.get("OBJECTID"))
            status = {"Public": "public", "Private": "private"}.get(p.get("Status"))
            recs.append(dict(name=str(p.get("SCHOOL_NAM") or "").strip().title(), level=str(p["LEVEL"]).lower(),
                             ownership=status, source="moe_2016" if "2016" in str(p.get("Source")) else "opendata_2007",
                             source_id=str(p.get("OBJECTID")), moe_ward=p.get("Ward"),
                             geometry=Point(p["X_Coord"], p["Y_Coord"])))
    return gpd.GeoDataFrame(recs, crs=WGS84)


OSM_OWNERSHIP = {"private": "private", "private_for_profit": "private", "individual": "private",
                 "government": "public", "central_government_deb": "public", "local_government_authority": "public",
                 "public": "public", "cbo": "community, faith or NGO", "community": "community, faith or NGO",
                 "religious": "community, faith or NGO", "religious_organization": "community, faith or NGO",
                 "ngo": "community, faith or NGO", "private_non_profit": "community, faith or NGO",
                 "private_not_for_profit": "community, faith or NGO"}
ISCED = {"0": "pre-primary", "1": "primary", "2": "secondary", "3": "secondary", "4": "other"}
EDU_TYPE = {"primary": "primary", "pre_primary": "pre-primary", "pre-primary": "pre-primary", "secondary": "secondary",
            "day_care": "pre-primary", "daycare": "pre-primary", "baby care centre": "pre-primary",
            "vocational": "other", "tertiary": "other"}


def osm_level(tags: dict) -> str | None:
    if tags.get("amenity") == "kindergarten":
        return "pre-primary"
    if tags.get("isced:level"):
        levels = {ISCED.get(v.strip()) for v in tags["isced:level"].split(";")} - {None}
        children = [lv for lv in LEVELS if lv in levels]
        if children:
            return " and ".join(children) if len(children) > 1 else children[0]
        if levels:
            return "other"
    t = EDU_TYPE.get(str(tags.get("education:type", "")).lower())
    if t:
        return t
    return level_from_name(tags.get("name", ""))


def read_osm() -> gpd.GeoDataFrame:
    els = json.loads(OSM_JSON.read_text())["elements"]
    recs = []
    for e in els:
        lon, lat = (e["lon"], e["lat"]) if e["type"] == "node" else (e["center"]["lon"], e["center"]["lat"])
        t = e["tags"]
        recs.append(dict(name=t.get("name", "").strip(), level=osm_level(t),
                         ownership=OSM_OWNERSHIP.get(str(t.get("operator:type", "")).lower()),
                         source="osm", source_id=f"{e['type']}/{e['id']}", moe_ward=None,
                         geometry=Point(lon, lat)))
    return gpd.GeoDataFrame(recs, crs=WGS84)


# ---------------------------------------------------------------- merge

def norm_name(name: str) -> str:
    words = re.findall(r"[A-Z0-9]+", name.upper().replace("'", ""))
    return " ".join(w for w in words if w not in GENERIC)


WEAK = {"COMMUNITY", "CHURCH", "CHRISTIAN", "MISSION", "CHILDREN", "CHILD", "CARE", "LEARNING", "DEVELOPMENT",
        "KIDS", "INTERNATIONAL", "NAIROBI", "MEMORIAL", "GIRLS", "BOYS", "OLD", "NEW", "ROAD", "ESTATE", "MODEL",
        "HOPE", "GRACE", "STAR", "JOY", "GOD", "GODS", "FAITH", "LIGHT", "VISION", "BRIGHT", "FUTURE", "CITY"}
PRE_WORDS = {"ECD", "ECDE", "NURSERY", "KINDERGARTEN", "DAYCARE", "BABY", "PRESCHOOL"}
LEVEL_WORDS = {"PRIMARY", "PRI", "SECONDARY", "SEC", "HIGH"}


def words(name: str) -> set[str]:
    return set(re.findall(r"[A-Z0-9]+", name.upper().replace("'", "")))


def distinctive(norm: str) -> set[str]:
    return {w for w in norm.split() if len(w) >= 3 and w not in WEAK}


def name_sim(a: pd.Series, b: pd.Series) -> float:
    """difflib ratio of the names without generic words; 0 if the names share no distinctive word."""
    if not a["norm"] or not b["norm"]:
        return 0.0
    da, db = distinctive(a["norm"]), distinctive(b["norm"])
    if not any(difflib.SequenceMatcher(None, x, y).ratio() >= 0.8 for x in da for y in db):
        return 0.0
    return difflib.SequenceMatcher(None, a["norm"], b["norm"]).ratio()


def conflict(a: pd.Series, b: pd.Series, d: float) -> bool:
    """True when two records cannot be the same school, even through a third record."""
    la, lb = a["level"], b["level"]
    if la in LEVELS and lb in LEVELS and la != lb:
        return True
    wa, wb = words(a["name"]), words(b["name"])
    if (wa & {"OLD", "NEW"}) != (wb & {"OLD", "NEW"}):
        return True
    if (wa & {"GIRLS", "BOYS"}) and (wb & {"GIRLS", "BOYS"}) and (wa & {"GIRLS", "BOYS"}) != (wb & {"GIRLS", "BOYS"}):
        return True
    for x, y in ((wa, wb), (wb, wa)):
        if "ACADEMY" in x and "ACADEMY" not in y and y & LEVEL_WORDS:
            return True
        if x & PRE_WORDS and not y & PRE_WORDS and y & LEVEL_WORDS:
            return True
    if a["source"] == b["source"] and d > SAME_SOURCE_M:
        return True
    return False


def merge(records: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Join records that pass either rule, nearest pairs first, never joining groups that hold a conflict."""
    g = records.to_crs(UTM).reset_index(drop=True)
    g["norm"] = g["name"].map(norm_name)
    # Official points may be in the old Arc 1960 datum (about 300 m off), so each official record is also tried
    # at its Arc 1960 -> WGS84 position.
    official = (g.source != "osm").to_numpy()
    alt = g.geometry.translate(xoff=ARC1960_DX, yoff=ARC1960_DY).where(official, g.geometry)
    positions = [g.geometry.to_numpy(), alt.to_numpy()]
    members = {i: [i] for i in range(len(g))}
    parent = list(range(len(g)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def mindist(i, j):
        return min(p[i].distance(q[j]) for p in positions for q in positions)

    cand = []
    for i, j in zip(*g.sindex.query(g.geometry.buffer(FAR_M + 300), predicate="intersects")):
        if i >= j:
            continue
        s = name_sim(g.loc[i], g.loc[j])
        if s < NAME_SIM:
            continue
        d = mindist(i, j)
        cross = g.at[i, "source"] != g.at[j, "source"]
        if d <= MERGE_M:
            cand.append((d, i, j, "near"))
        elif cross and s >= FAR_SIM and d <= FAR_M:
            cand.append((d, i, j, "same name"))
    rule, blocked = {}, 0
    for d, i, j, why in sorted(cand):
        ri, rj = find(i), find(j)
        if ri == rj:
            continue
        if any(conflict(g.loc[a], g.loc[b], mindist(a, b)) for a in members[ri] for b in members[rj]):
            blocked += 1
            continue
        parent[ri] = rj
        members[rj] += members.pop(ri)
        rule[(i, j)] = why
    log.info("merge: %d joins by the 50 m rule, %d by the same-name rule, %d blocked by a conflict",
             sum(v == "near" for v in rule.values()), sum(v == "same name" for v in rule.values()), blocked)
    g["cluster"] = [find(i) for i in range(len(g))]
    log.info("merge pairs: %d by the 50 m rule, %d by the same-name rule",
             sum(v == "near" for v in rule.values()), sum(v == "same name" for v in rule.values()))

    def pick(cl: pd.DataFrame) -> dict:
        osm = cl[cl.source == "osm"]
        moe = cl[cl.source != "osm"]
        loc = (osm if len(osm) else cl.sort_values("source", key=lambda s: s.ne("moe_2016"))).iloc[0]
        named = cl[cl.name != ""]
        name = (osm[osm.name != ""] if len(osm[osm.name != ""]) else named).name
        levels = [lv for lv in cl.level.dropna() if lv]
        level = next((lv for lv in levels if lv in LEVELS or " and " in lv), levels[0] if levels else "unknown")
        own = next((o for o in list(moe.ownership.dropna()) + list(osm.ownership.dropna())), "unknown")
        return dict(name=name.iloc[0] if len(name) else "", level=level, ownership=own,
                    sources=";".join(sorted(set(cl.source))), source_ids=";".join(cl.source_id),
                    n_records=len(cl),
                    location=("OpenStreetMap" if len(osm) else
                              "official list only; may be up to about 300 m off"),
                    geometry=loc.geometry)

    return gpd.GeoDataFrame([pick(cl) for _, cl in g.groupby("cluster", sort=False)], crs=UTM)


# ---------------------------------------------------------------- side counts for the report

def source_counts(county_utm) -> dict:
    hot = gpd.read_parquet(HOT_PARQUET).to_crs(UTM)
    hot = hot[hot.amenity.isin(["school", "kindergarten"])]
    hot_in = hot[hot.geometry.representative_point().within(county_utm)]
    osm_ids = {f"{e['type']}/{e['id']}" for e in json.loads(OSM_JSON.read_text())["elements"]}
    osk = pd.read_csv(OSK_CSV, usecols=["WKT", "osm:id", "osm:amenity"], dtype=str)
    osk = gpd.GeoDataFrame(osk, geometry=gpd.GeoSeries.from_wkt(osk["WKT"]), crs=WGS84).to_crs(UTM)
    osk_in = osk[osk.geometry.representative_point().within(county_utm)]
    osk_ids = osk_in["osm:id"].dropna()
    osk_gone = sum(1 for i in osk_ids if not any(f"{t}/{i.split('/')[-1]}" in osm_ids for t in ("node", "way", "relation")))
    return dict(hot_osm_export_schools_kindergartens_in_county=int(len(hot_in)),
                open_schools_kenya_in_county=int(len(osk_in)),
                open_schools_kenya_no_longer_in_osm=int(osk_gone))


def main() -> None:
    if "--fetch" in sys.argv or not OSM_JSON.exists():
        fetch()
    county = gpd.read_file(BOUNDARY).to_crs(UTM).union_all()
    moe, osm = read_moe(), read_osm()
    counts = {"moe_records_nairobi": len(moe),
              "moe_2016": int((moe.source == "moe_2016").sum()),
              "opendata_2007": int((moe.source == "opendata_2007").sum()),
              "osm_records_bbox": len(osm)}
    allrec = pd.concat([moe, osm], ignore_index=True)
    allrec = allrec[allrec.to_crs(UTM).within(county)]
    counts["moe_records_in_county"] = int((allrec.source != "osm").sum())
    counts["moe_records_outside_county"] = len(moe) - counts["moe_records_in_county"]
    counts["osm_records_in_county"] = int((allrec.source == "osm").sum())
    schools = merge(allrec)
    schools["school_id"] = [f"S{i:05d}" for i in range(1, len(schools) + 1)]
    counts["merged_schools"] = len(schools)
    counts["records_merged_away"] = len(allrec) - len(schools)
    counts.update(source_counts(county))
    counts["by_level"] = schools.level.value_counts().to_dict()
    counts["by_ownership"] = schools.ownership.value_counts().to_dict()
    counts["by_sources"] = schools.sources.value_counts().to_dict()
    (DIR / "source_counts.json").write_text(json.dumps(counts, indent=2))
    log.info("schools: %s", json.dumps(counts))

    counts["by_location"] = schools.location.value_counts().to_dict()
    (DIR / "source_counts.json").write_text(json.dumps(counts, indent=2))
    cols = ["school_id", "name", "level", "ownership", "sources", "source_ids", "n_records", "location", "geometry"]
    schools[cols].to_crs(WGS84).to_file(OUT, driver="GeoJSON")
    log.info("wrote %s (%d schools)", OUT, len(schools))


if __name__ == "__main__":
    main()
