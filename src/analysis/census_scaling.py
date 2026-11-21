"""WorldPop 2025 ward populations scaled to the 2019 census sub-county totals (prompt v3, task 5).

The 2019 census reports Nairobi by 11 census sub-counties (Dagoretti, Embakasi, ...), which are not the 17 IEBC
sub-counties (constituencies) of our ward layer, and no open boundary map of them exists. So each ward is assigned
to a census sub-county by name, using the census hierarchy (division, location and sub-location names in
Volume II table 2.4). The assignment and a confidence level are in WARD_TO_CENSUS below and in the output table.

Method: grow each census sub-county total from census night (24/25 August 2019) to mid-2025 with Nairobi's
intercensal growth rate, then multiply every ward's WorldPop total by (grown census total / WorldPop total of the
wards assigned to that sub-county). This fixes how many people each census sub-county holds; it does not change
how WorldPop spreads people between wards inside a census sub-county.

    uv run python -m src.analysis.census_scaling
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CENSUS = Path.home() / 'Desktop/kenya-2019-census-csv/data/csv/kenya_2019_census_population_all_admin_levels.csv'
WARDS = ROOT / 'analysis/tables/ward_stats.csv'
TOP = ROOT / 'analysis/tables/top_wards.csv'
OUT = ROOT / 'analysis/tables/ward_population_scaled.csv'
OUT_JSON = ROOT / 'analysis/census_scaling_results.json'

# Nairobi's census counts: 2009 KPHC (KNBS 2010, Volume IA) and 2019 KPHC (KNBS 2019, Volume II table 2.2).
NAIROBI_2009 = 3_138_369
NAIROBI_2019 = 4_397_073
YEARS_2009_2019 = 10.0          # both censuses were taken on the night of 24/25 August
YEARS_2019_TO_MID_2025 = 5.85   # 25 August 2019 to 1 July 2025

# ward -> (census sub-county, confidence, basis). high: the ward name is, or is inside, a census location or
# sub-location of that sub-county. medium: the ward is not named in the census but lies between units that are.
# low: the ward could belong to either of two census sub-counties.
WARD_TO_CENSUS = {
    # Dagoretti: divisions Kawangware and Waithaka
    'Gatina': ('DAGORETTI', 'high', 'location Gatina'),
    'Kabiro': ('DAGORETTI', 'high', 'sub-location Kabiro (location Kawangware)'),
    'Kawangware': ('DAGORETTI', 'high', 'location Kawangware'),
    'Ngando': ('DAGORETTI', 'high', 'location Ngando'),
    'Riruta': ('DAGORETTI', 'high', 'location Riruta'),
    'Mutu-ini': ('DAGORETTI', 'high', 'location Mutuini'),
    'Uthiru/Ruthimitu': ('DAGORETTI', 'high', 'locations Uthiru and Ruthimitu'),
    'Waithaka': ('DAGORETTI', 'high', 'location Waithaka'),
    # Westlands: divisions Highridge, Kangemi and Kilimani
    'Kileleshwa': ('WESTLANDS', 'high', 'location Kileleshwa (division Kilimani)'),
    'Kilimani': ('WESTLANDS', 'high', 'location Kilimani'),
    'Kangemi': ('WESTLANDS', 'high', 'location Kangemi'),
    'Kitisuru': ('WESTLANDS', 'high', 'location Kitisuru'),
    'Parklands/Highridge': ('WESTLANDS', 'high', 'locations Parklands and Highridge'),
    'Karura': ('WESTLANDS', 'medium', 'Westlands constituency; between locations Kitisuru and Highridge'),
    'Mountain View': ('WESTLANDS', 'medium', 'Westlands constituency; next to location Kangemi'),
    # Embakasi: divisions Embakasi, Kayole and Umoja
    'Embakasi': ('EMBAKASI', 'high', 'location Embakasi'),
    'Imara Daima': ('EMBAKASI', 'high', 'location Imara Daima'),
    'Kwa Njenga': ('EMBAKASI', 'high', 'location Mukuru kwa Njenga'),
    'Kwa Reuben': ('EMBAKASI', 'high', 'location Mukuru kwa Njenga'),
    'Pipeline': ('EMBAKASI', 'medium', 'between locations Mukuru kwa Njenga and Embakasi'),
    'Kware': ('EMBAKASI', 'medium', 'between locations Mukuru kwa Njenga and Embakasi'),
    'Kayole Central': ('EMBAKASI', 'high', 'location Kayole'),
    'Kayole South': ('EMBAKASI', 'high', 'location Kayole'),
    'Komarock': ('EMBAKASI', 'high', 'location Komarock'),
    'Matopeni/Spring Valley': ('EMBAKASI', 'medium', 'between locations Kayole and Komarock'),
    'Upper Savannah': ('EMBAKASI', 'high', 'location Savannah'),
    'Lower Savannah': ('EMBAKASI', 'high', 'location Savannah'),
    'Umoja I': ('EMBAKASI', 'high', 'location Umoja'),
    'Umoja II': ('EMBAKASI', 'high', 'location Umoja'),
    'Utawala': ('EMBAKASI', 'high', 'sub-location Utawala (location Embakasi)'),
    # Njiru: divisions Dandora, Njiru and Ruai
    'Dandora Area I': ('NJIRU', 'high', 'location Dandora I & II'),
    'Dandora Area II': ('NJIRU', 'high', 'location Dandora I & II'),
    'Dandora Area III': ('NJIRU', 'high', 'location Dandora B'),
    'Dandora Area IV': ('NJIRU', 'high', 'location Dandora B'),
    'Kariobangi South': ('NJIRU', 'high', 'location Kariobangi South'),
    'Mowlem': ('NJIRU', 'high', 'sub-location Mowlem (location Kariobangi South)'),
    'Kayole North': ('NJIRU', 'high', 'location Kayole North'),
    'Mihango': ('NJIRU', 'high', "location Mihang'o"),
    'Njiru': ('NJIRU', 'high', 'location Njiru'),
    'Ruai': ('NJIRU', 'high', 'locations Ruai and Kamulu'),
    # Kasarani: divisions Githurai, Kariobangi North, Kasarani and Roysambu
    'Githurai': ('KASARANI', 'high', 'location Githurai'),
    'Kahawa West': ('KASARANI', 'high', 'location Kahawa West'),
    'Zimmerman': ('KASARANI', 'high', 'location Zimmerman'),
    'Kahawa': ('KASARANI', 'medium', 'Roysambu constituency; next to locations Kahawa West and Githurai'),
    'Roysambu': ('KASARANI', 'high', 'location Roysambu'),
    'Baba Dogo': ('KASARANI', 'high', 'location Baba Dogo'),
    'Korogocho': ('KASARANI', 'high', 'location Korogocho'),
    'Kariobangi North': ('KASARANI', 'high', 'location Kariobangi North'),
    'Lucky Summer': ('KASARANI', 'high', 'sub-location Lucky Summer (location Baba Dogo)'),
    'Mathare North': ('KASARANI', 'high', 'sub-location Mathare North (location Ruaraka)'),
    'Utalii': ('KASARANI', 'high', 'location Utalii'),
    'Kasarani': ('KASARANI', 'high', 'location Kasarani'),
    'Mwiki': ('KASARANI', 'high', 'location Mwiki'),
    'Clay City': ('KASARANI', 'high', 'sub-location Clay City (location Kasarani)'),
    # Kamukunji: divisions Eastleigh and Pumwani
    'Airbase': ('KAMUKUNJI', 'high', 'location Airbase'),
    'California': ('KAMUKUNJI', 'high', 'sub-location California (location Eastleigh South)'),
    'Eastleigh North': ('KAMUKUNJI', 'high', 'location Eastleigh North'),
    'Eastleigh South': ('KAMUKUNJI', 'high', 'location Eastleigh South'),
    'Pumwani': ('KAMUKUNJI', 'high', 'location Pumwani'),
    # Starehe: divisions CBD, Central and South B
    'Nairobi Central': ('STAREHE', 'high', 'division CBD'),
    'Ngara': ('STAREHE', 'high', 'location Ngara'),
    'Pangani': ('STAREHE', 'high', 'location Pangani'),
    'Ziwani/Kariokor': ('STAREHE', 'high', 'location Kariokor'),
    'Landimawe': ('STAREHE', 'high', 'location Landmawe'),
    'Nairobi South': ('STAREHE', 'medium', 'division South B (locations Landmawe and Mukuru Nyayo)'),
    # Makadara: divisions Bahati, Makadara and Viwandani
    'Makongeni': ('MAKADARA', 'high', 'location Makongeni'),
    'Maringo/Hamza': ('MAKADARA', 'high', 'location Maringo'),
    'Viwandani': ('MAKADARA', 'high', 'location Viwandani'),
    'Harambee': ('MAKADARA', 'medium', 'between locations Makadara and Bahati'),
    # Mathare: divisions Huruma and Mathare
    'Huruma': ('MATHARE', 'high', 'location Huruma'),
    'Kiamaiko': ('MATHARE', 'high', 'sub-location Kiamaiko (location Huruma)'),
    'Hospital': ('MATHARE', 'medium', 'location Mathare; part of the valley is in sub-location Mathare 4A (Kasarani)'),
    'Mabatini': ('MATHARE', 'medium', 'location Mathare; part of the valley is in sub-location Mathare 4A (Kasarani)'),
    'Mlango Kubwa': ('MATHARE', 'medium', 'location Mathare'),
    'Ngei': ('MATHARE', 'medium', 'location Mathare'),
    # Kibra: divisions Kibera, Laini Saba and Woodley
    'Laini Saba': ('KIBRA', 'high', 'location Laini Saba'),
    'Lindi': ('KIBRA', 'high', 'sub-location Lindi (location Kibera)'),
    'Makina': ('KIBRA', 'high', 'sub-location Makina (location Kibera)'),
    "Sarang'ombe": ('KIBRA', 'high', 'location Sarangombe'),
    'Woodley/Kenyatta Golf Course': ('KIBRA', 'high', 'division Woodley (locations Woodley, Kenyatta, Golf Course)'),
    # Lang'ata: divisions Karen and Nairobi West
    'Karen': ("LANG'ATA", 'high', 'location Karen'),
    'Nairobi West': ("LANG'ATA", 'high', 'location Nairobi West'),
    'Mugumo-ini': ("LANG'ATA", 'high', 'location Mugumoini'),
    'Nyayo Highrise': ("LANG'ATA", 'high', 'location Highrise'),
    'South C': ("LANG'ATA", 'high', 'sub-location South C (location Nairobi West)'),
}


def main() -> dict:
    census = pd.read_csv(CENSUS)
    sc = census[(census.county == 'NAIROBI CITY') & (census.level == 'subcounty')].set_index('name')['total']
    wards = pd.read_csv(WARDS)[['ward_name', 'pop_total', 'lst_median_c', 'rank_hottest']]
    missing = set(wards.ward_name) - set(WARD_TO_CENSUS)
    extra = set(WARD_TO_CENSUS) - set(wards.ward_name)
    assert not missing and not extra, (missing, extra)

    rate = (NAIROBI_2019 / NAIROBI_2009) ** (1 / YEARS_2009_2019) - 1
    grow = (1 + rate) ** YEARS_2019_TO_MID_2025

    m = pd.DataFrame([(w, *v) for w, v in WARD_TO_CENSUS.items()],
                     columns=['ward_name', 'census_subcounty', 'assignment_confidence', 'assignment_basis'])
    df = wards.merge(m, on='ward_name')
    by_sc = df.groupby('census_subcounty')['pop_total'].sum()
    factors = (sc * grow) / by_sc
    df['census_subcounty_2019'] = df.census_subcounty.map(sc)
    df['census_subcounty_2025_grown'] = (df.census_subcounty_2019 * grow).round().astype(int)
    df['scale_factor'] = df.census_subcounty.map(factors).round(3)
    df['pop_worldpop2025'] = df.pop_total.round().astype(int)
    df['pop_scaled_to_census'] = (df.pop_total * df.census_subcounty.map(factors)).round().astype(int)
    df['change'] = df.pop_scaled_to_census - df.pop_worldpop2025
    df['change_pct'] = (100 * df.change / df.pop_worldpop2025).round(1)
    cols = ['ward_name', 'census_subcounty', 'assignment_confidence', 'assignment_basis', 'pop_worldpop2025',
            'pop_scaled_to_census', 'change', 'change_pct', 'scale_factor', 'census_subcounty_2019',
            'census_subcounty_2025_grown', 'lst_median_c', 'rank_hottest']
    df = df[cols].sort_values(['census_subcounty', 'ward_name'])
    df.to_csv(OUT, index=False)

    top = pd.read_csv(TOP)['ward_name'].tolist()
    t = df.set_index('ward_name').loc[top]
    woodley = df.set_index('ward_name').loc['Woodley/Kenyatta Golf Course']
    res = {
        'growth_rate_pct_per_year': round(100 * rate, 2),
        'growth_factor_2019_to_mid_2025': round(grow, 4),
        'growth_source': 'Intercensal geometric rate for Nairobi City County, KNBS census counts 2009 (3,138,369) '
                         'and 2019 (4,397,073), both on the night of 24/25 August',
        'county_census_2019': NAIROBI_2019,
        'county_grown_mid_2025': int(round(NAIROBI_2019 * grow)),
        'county_worldpop2025_ward_sum': int(round(wards.pop_total.sum())),
        'factors_by_census_subcounty': factors.round(3).to_dict(),
        'woodley': dict(worldpop2025=int(woodley.pop_worldpop2025), scaled=int(woodley.pop_scaled_to_census),
                        census2019_woodley_division=int(census[(census.level == 'division') & (census['name'] == 'WOODLEY')
                                                              & (census.county == 'NAIROBI CITY')]['total'].iloc[0])),
        'top10_pop_weighted_wards': dict(names=top, worldpop2025=int(t.pop_worldpop2025.sum()),
                                         scaled=int(t.pop_scaled_to_census.sum()),
                                         by_ward={w: [int(r.pop_worldpop2025), int(r.pop_scaled_to_census)] for w, r in t.iterrows()}),
        'wards_by_confidence': df.assignment_confidence.value_counts().to_dict(),
        'table': str(OUT.relative_to(ROOT)),
        'script': 'src/analysis/census_scaling.py',
    }
    OUT_JSON.write_text(json.dumps(res, indent=2))
    return res


if __name__ == '__main__':
    print(json.dumps(main(), indent=2))
