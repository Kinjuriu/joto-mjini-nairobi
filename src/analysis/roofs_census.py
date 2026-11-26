# Copyright (c) 2026 Stephane Ngugi. All rights reserved. See LICENSE.
"""Iron sheet roofs from the 2019 census, by Nairobi census sub-county, set against ward surface temperature.

Census: KNBS 2019 Volume IV table 2.12 (share of conventional households by dominant roofing material),
extracted in the kenya-2019-census-csv repository. Census sub-counties (11) are administrative units, not the
17 IEBC constituencies our wards belong to, and no open boundary map of them was found. Wards are therefore
linked to a census sub-county by name only, with this rule:

1. a ward matches a census sub-county if its name (or one part of a name such as "Maringo/Hamza") equals the
   name of a division, location or sub-location in that sub-county in Volume II table 2.4;
2. the match is kept only if exactly one census sub-county matches, and at least one other ward of the same
   constituency matches the same census sub-county (this drops chance matches of common names, for example
   Matopeni/Spring Valley in Embakasi Central against a Spring Valley location in Westlands).

Wards without a kept match are left out of the comparison and listed in the output.

    uv run python -m src.analysis.roofs_census
"""
import collections
import re
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
CENSUS = Path.home() / 'Desktop' / 'kenya-2019-census-csv' / 'data' / 'csv'
ROOFS = CENSUS / 'kenya_2019_census_roofing_material_by_county_subcounty.csv'
UNITS = CENSUS / 'kenya_2019_census_population_all_admin_levels.csv'
WARDS = ROOT / 'analysis' / 'tables' / 'ward_stats.csv'
WARD_LAYER = ROOT / 'site' / 'public' / 'data' / 'wards.geojson'
OUT_ROOFS = ROOT / 'site' / 'public' / 'data' / 'roofs_by_subcounty.csv'
OUT_MATCH = ROOT / 'analysis' / 'tables' / 'ward_census_subcounty_match.csv'
OUT_COMPARE = ROOT / 'analysis' / 'tables' / 'roofs_vs_ward_heat.csv'

MATERIALS = ['iron_sheets_pct', 'concrete_cement_pct', 'tiles_pct', 'asbestos_sheet_pct', 'decra_versatile_pct',
             'nylon_cartons_cardboard_pct', 'tin_cans_pct', 'grass_twigs_pct', 'makuti_thatch_pct', 'dung_mud_pct',
             'canvas_tents_pct', 'shingles_pct', 'not_stated_pct']


def norm(s: str) -> str:
    return re.sub(r'[^A-Z]', '', s.upper())


def roofs() -> pd.DataFrame:
    r = pd.read_csv(ROOFS)
    r = r[(r.county == 'NAIROBI CITY') | (r['name'] == 'NAIROBI CITY')]
    r = r[r.breakdown == 'all']
    out = r[['level', 'name', 'conventional_households'] + MATERIALS].rename(columns={'name': 'census_subcounty'})
    out['level'] = out['level'].replace({'subcounty': 'census_subcounty'})
    out['source'] = 'KNBS 2019 Kenya Population and Housing Census, Volume IV, table 2.12'
    out['source_page'] = r['page'].values
    out['extracted_by'] = 'https://github.com/Kinjuriu/kenya-2019-census-csv'
    return out


def match_wards() -> pd.DataFrame:
    import json
    units = pd.read_csv(UNITS)
    units = units[(units.county == 'NAIROBI CITY') & units.level.isin(['division', 'location', 'sublocation'])]
    index = collections.defaultdict(set)
    for _, u in units.iterrows():
        index[norm(u['name'])].add(u['subcounty'])
    wards = [f['properties'] for f in json.load(open(WARD_LAYER))['features']]
    rows = []
    for w in wards:
        parts = {norm(w['ward_name'])} | {norm(x) for x in re.split(r'[/-]', w['ward_name']) if x.strip()}
        found = sorted(set().union(*(index.get(p, set()) for p in parts)))
        rows.append({'ward_id': w['ward_id'], 'ward_name': w['ward_name'], 'constituency': w['subcounty'],
                     'name_matches': ';'.join(found)})
    m = pd.DataFrame(rows)
    single = m[m.name_matches.str.count(';') == 0].query("name_matches != ''")
    support = single.groupby(['constituency', 'name_matches']).size()
    def keep(r):
        if r.name_matches == '' or ';' in r.name_matches:
            return ''
        return r.name_matches if support.get((r.constituency, r.name_matches), 0) >= 2 else ''
    m['census_subcounty'] = m.apply(keep, axis=1)
    m['rule'] = m.apply(lambda r: 'kept' if r.census_subcounty else
                        ('no name match' if r.name_matches == '' else
                         'more than one census sub-county' if ';' in r.name_matches else
                         'only ward of its constituency matching this census sub-county'), axis=1)
    return m


def main():
    r = roofs()
    r.to_csv(OUT_ROOFS, index=False)
    m = match_wards()
    m.to_csv(OUT_MATCH, index=False)
    ws = pd.read_csv(WARDS)[['ward_id', 'lst_median_c', 'area_km2', 'rank_hottest', 'rank_pop_weighted',
                             'pop_weighted_lst_c']]
    j = m.merge(ws, on='ward_id')
    kept = j[j.census_subcounty != '']
    agg = kept.groupby('census_subcounty').apply(lambda g: pd.Series({
        'wards_matched': len(g),
        'ward_median_lst_c_area_weighted': (g.lst_median_c * g.area_km2).sum() / g.area_km2.sum(),
        'hottest_ward_lst_c': g.lst_median_c.max(),
        'wards_in_ten_hottest': int((g.rank_hottest <= 10).sum()),
        'wards_in_ten_hottest_where_people_live': int((g.rank_pop_weighted <= 10).sum()),
    }), include_groups=False).reset_index()
    sub = r[r.level == 'census_subcounty'][['census_subcounty', 'iron_sheets_pct', 'concrete_cement_pct',
                                            'conventional_households']]
    cmp_ = sub.merge(agg, on='census_subcounty', how='left').sort_values('iron_sheets_pct', ascending=False)
    cmp_.to_csv(OUT_COMPARE, index=False)
    ok = cmp_.dropna(subset=['ward_median_lst_c_area_weighted'])
    rho, p = spearmanr(ok.iron_sheets_pct, ok.ward_median_lst_c_area_weighted)
    print(cmp_.round(1).to_string(index=False))
    print(f'\nWards kept: {len(kept)} of {len(m)}; rule outcome: {m.rule.value_counts().to_dict()}')
    print(f'Spearman (iron sheet share vs area-weighted ward median), {len(ok)} census sub-counties: '
          f'rho = {rho:.2f}, p = {p:.2f}')
    t10 = j[j.rank_hottest <= 10][['ward_name', 'constituency', 'census_subcounty', 'lst_median_c']]
    tp = j[j.rank_pop_weighted <= 10][['ward_name', 'constituency', 'census_subcounty', 'pop_weighted_lst_c']]
    print('\nTen hottest wards:\n', t10.sort_values('lst_median_c', ascending=False).round(1).to_string(index=False))
    print('\nTen hottest wards where people live:\n', tp.sort_values('pop_weighted_lst_c', ascending=False).round(1).to_string(index=False))


if __name__ == '__main__':
    main()
