"""Check the merged school map against the Nairobi City County list of public ECD centres and primary schools.

Source: Nairobi City County Education Department, "Data on Nairobi public ECD centres & primary schools and
locations" (PDF exported from Excel on 25 June 2014; 225 rows; name, district, zone and a written location, no
coordinates). File: data/raw/schools/nairobi_county_2014/Nairobi County Public-Primary-Schools.pdf.

The list has no coordinates, so it cannot add points to the map. It is used only as a completeness check: for each
county school we look for a school in data/processed/nairobi_schools.geojson whose name matches, using the same
name rules as the merge in src/pipeline/s10_schools.py (generic words removed, at least one shared distinctive word,
difflib ratio at least NAME_SIM). Matches are by name alone and are listed in the CSV for checking by eye.

Run: uv run python -m src.analysis.county_school_list
Writes: data/processed/county_school_list_2014.csv, analysis/county_school_list_check.json
"""
from __future__ import annotations

import json
import re
import subprocess

import geopandas as gpd
import pandas as pd

from src.config import PROCESSED, RAW, get_logger
from src.pipeline.s10_schools import NAME_SIM, PRE_WORDS, name_sim, norm_name, words

log = get_logger("county_school_list")

PDF = RAW / "schools" / "nairobi_county_2014" / "Nairobi County Public-Primary-Schools.pdf"
MAP = PROCESSED / "nairobi_schools.geojson"
OUT_CSV = PROCESSED / "county_school_list_2014.csv"
OUT_JSON = PROCESSED.parent.parent / "analysis" / "county_school_list_check.json"
DISTRICTS = ["DAGORETTI", "EMBAKASI", "KAMUKUNJI", "KASARANI", "LANG'ATA", "MAKADARA", "STAREHE", "WESTLANDS"]
ROW = re.compile(r"^\s*(\d{1,3})\s+(.+?)\s{2,}(" + "|".join(DISTRICTS) + r")\s+(.+?)\s{2,}(.*)$")
NAME_ONLY = re.compile(r"^\s*(\d{1,3})\s+(\S.*?)\s*$")
TAIL = re.compile(r"^\s{20,}(" + "|".join(DISTRICTS) + r")\s+(.+?)\s{2,}(.*)$")
# Spelling and abbreviations, applied to both lists before the name rules.
SPELLING = {"CURSERY": "NURSERY", "NUSERY": "NURSERY", "NUR": "NURSERY", "AINSWOTH": "AINSWORTH",
            "KAWAHA": "KAHAWA", "REHAB": "REHABILITATION", "PARKROAD": "PARK ROAD", "PRY": "PRIMARY", "PRI": "PRIMARY"}
# Checked by eye: the map school is the county school, but the names differ too much for the rules.
MANUAL = {195: "S02897",   # Mathare Technical Special -> Mathare Special Training Centre (Juja Road)
          208: "S00651"}   # Visa Oshwal Primary - Nairobi -> Visa Oshwal Primary School (not Oshwal Academy)


def parse() -> pd.DataFrame:
    text = subprocess.run(["pdftotext", "-layout", str(PDF), "-"], capture_output=True, text=True, check=True).stdout
    rows, pending = [], None
    for line in text.splitlines():
        m = ROW.match(line)
        if m:
            rows.append(dict(sno=int(m[1]), name=m[2].strip(), district=m[3], zone=m[4].strip(), location=m[5].strip()))
            pending = None
            continue
        t = TAIL.match(line)
        if t and pending is not None:     # a name whose district and zone wrapped onto the next line
            rows.append(dict(sno=pending[0], name=pending[1], district=t[1], zone=t[2].strip(), location=t[3].strip()))
            pending = None
            continue
        n = NAME_ONLY.match(line)
        if n and not any(d in line for d in DISTRICTS) and not line.startswith("S/NO"):
            pending = (int(n[1]), n[2])
    df = pd.DataFrame(rows).drop_duplicates("sno").sort_values("sno").reset_index(drop=True)
    missing = sorted(set(range(1, df.sno.max() + 1)) - set(df.sno))
    if missing:
        log.warning("rows not parsed: %s", missing)
    return df


def fix(name: str) -> str:
    """Upper case, initials joined (G.S.U. and S S D become GSU and SSD), spelling and abbreviations expanded."""
    s = re.sub(r"\b([A-Z])\.(?=[A-Z]\b|[A-Z]\.)", r"\1", name.upper())
    s = re.sub(r"\b([A-Z]) (?=[A-Z]\b)", r"\1", s)
    s = re.sub(r"[^A-Z0-9' ]", " ", s)
    return " ".join(SPELLING.get(w, w) for w in s.split())


def main() -> None:
    county = parse()
    county["is_ecd"] = county.name.map(lambda s: bool(words(fix(s)) & PRE_WORDS))
    schools = gpd.read_file(MAP)
    # The county list has only ECD centres and primary (some special) schools, so secondary schools are left out.
    schools = schools[~schools.level.isin(["secondary"])].reset_index(drop=True)
    schools["norm"] = schools.name.fillna("").map(lambda n: norm_name(fix(n)))
    out = []
    for _, r in county.iterrows():
        a = pd.Series(dict(norm=norm_name(fix(r["name"]))))
        if r["sno"] in MANUAL:
            best, how = schools.index[schools.school_id == MANUAL[r["sno"]]][0], "checked by eye"
            ok, sim = True, None
        else:
            exact = schools.norm == a["norm"]   # also catches names made only of common words (Nairobi, City)
            sims = exact.astype(float) if exact.any() and a["norm"] else schools.apply(lambda b: name_sim(a, b), axis=1)
            best = sims.idxmax()
            sim = round(float(sims[best]), 2)
            ok, how = sim >= NAME_SIM, "same name" if exact.any() and a["norm"] else "similar name"
        out.append(dict(r, matched=bool(ok), match_how=how if ok else "", match_sim=sim,
                        match_school_id=schools.at[best, "school_id"] if ok else "",
                        match_name=schools.at[best, "name"] if ok else "",
                        match_level=schools.at[best, "level"] if ok else "",
                        match_sources=schools.at[best, "sources"] if ok else ""))
    res = pd.DataFrame(out)
    res.to_csv(OUT_CSV, index=False)
    prim = res[~res.is_ecd]
    summary = dict(
        source="Nairobi City County Education Department, public ECD centres and primary schools, June 2014 (PDF)",
        rows=len(res), ecd_rows=int(res.is_ecd.sum()), school_rows=len(prim),
        matched=int(res.matched.sum()), matched_schools=int(prim.matched.sum()),
        matched_ecd=int(res[res.is_ecd].matched.sum()),
        match_rule=f"name only (secondary schools excluded): same name after normalising, else s10_schools.name_sim >= {NAME_SIM}; {len(MANUAL)} checked by eye",
        unmatched=res.loc[~res.matched, ["sno", "name", "district", "zone", "location"]].to_dict("records"),
        script="src/analysis/county_school_list.py", output_csv=str(OUT_CSV.relative_to(PROCESSED.parent.parent)))
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    log.info("county list: %d rows (%d ECD); matched %d (%d of %d schools, %d ECD)", summary["rows"],
             summary["ecd_rows"], summary["matched"], summary["matched_schools"], summary["school_rows"],
             summary["matched_ecd"])


if __name__ == "__main__":
    main()
