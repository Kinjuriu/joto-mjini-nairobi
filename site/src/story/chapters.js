// The scrolling map story, as data (chunk 3). Each chapter is one card and one map state.
//
// Card text uses sentences and numbers from analysis/FINDINGS.md. Numbers are written as {{path|format}}
// and filled at build time from analysis/results.json by the Vite plugin in vite.config.js, which also
// renders these cards into index.html (so they exist without JavaScript). Text marked [[COPY: ...]] is a
// placeholder for Stephane's own writing.
//
// Map fields: basemap ('satellite' | 'light'), layers [{id, opacity}], center [lon, lat], zoom (desktop),
// mobileZoom, chip (date chip text), legend (manifest layer id) and legendTitle, highlight (ward names).

const LIGHT_OP = 0.85;  // data over imagery, county-wide views
const SAT_OP = 0.75;    // data over imagery, close-up views
const COUNTY = [36.86, -1.29];
const base = (extra) => [{ id: 'county-line', opacity: 1 }, ...extra];
// The ten hottest wards where people live (analysis/results.json q4.top10_pop_weighted).
const TOP10 = ['Kangemi', 'Viwandani', 'Kabiro', 'Dandora Area I', 'Baba Dogo', 'Imara Daima', 'Kayole South', 'Kariobangi North', 'Kiamaiko', 'Kawangware'];
// Five hottest and five coolest wards where people live (analysis/results_extra.json wards_top5).
const HOT5 = ['Kangemi', 'Viwandani', 'Kabiro', 'Dandora Area I', 'Baba Dogo'];
const COOL5 = ['Kileleshwa', 'Mutu-ini', 'Karura', 'Kitisuru', 'Karen'];

export const CHAPTERS = [
  // ---------------------------------------------------------------- Story block A: Nairobi's heat divide
  {
    id: 'space', block: 'A', basemap: 'satellite', center: COUNTY, zoom: 10.3, mobileZoom: 9.4,
    layers: base([]),
    chip: 'Sentinel-2 cloudless, 2025', legend: null,
    card: {
      title: 'Nairobi from space',
      // DRAFT 16 Nov (Claude), for Stephane to edit.
      text: 'Nairobi County from space, in a cloud-free picture from the European Sentinel-2 satellites. The white line is the county boundary.',
    },
  },
  {
    id: 'divide', block: 'A', basemap: 'satellite', center: COUNTY, zoom: 10.3, mobileZoom: 9.4,
    layers: base([{ id: 'heat-diff', opacity: LIGHT_OP }, { id: 'wards-line', opacity: 1 }, { id: 'ward-labels', opacity: 1 }]),
    // Pulsing circles on the largest patch of the hottest and of the coolest tenth of the land (found in the
    // hot-season median raster with a 1.2 km moving window; the labels read their numbers from this card).
    pulses: [
      { at: [37.063, -1.237], tone: 'hot', fact: 'Hottest tenth of the land', place: 'largest patch near Ruai' },
      { at: [36.829, -1.240], tone: 'cool', fact: 'Coolest tenth', place: 'largest patch in Karura Forest' },
    ],
    chip: 'January to March mornings, 2023 to 2026', legend: 'heat-diff',
    card: {
      title: 'The heat divide',
      facts: [
        ['Half of the county\'s ground', 'hotter than {{q1.county_median_c|c}} at the surface'],
        ['Hottest tenth of the land', '{{q1.hottest10pct_land_mean_c|c}}'],
        ['Coolest tenth', '{{q1.coolest10pct_land_mean_c|c}}'],
      ],
      note: 'Orange and red ground was hotter than the county median; blue was cooler.',
    },
  },
  {
    id: 'centre', block: 'A', basemap: 'satellite', center: [36.840, -1.296], zoom: 13.4, mobileZoom: 12.4,
    layers: [{ id: 'comparison-areas', opacity: 1 }],
    chip: 'Satellite image', legend: null,
    card: {
      title: 'City centre and Industrial Area',
      // DRAFT 16 Nov (Claude), for Stephane to edit.
      text: 'The city centre and, to its south-east, the Industrial Area: almost all roof, road and paved yard.',
    },
  },
  {
    id: 'centre-heat', block: 'A', basemap: 'satellite', center: [36.840, -1.296], zoom: 13.4, mobileZoom: 12.4,
    layers: [{ id: 'heat-diff', opacity: SAT_OP }, { id: 'comparison-areas', opacity: 1 }],
    chip: 'January to March mornings, 2023 to 2026', legend: 'heat-diff',
    card: {
      title: 'The same view, by surface temperature',
      facts: [
        ['Industrial Area', '{{q2.Industrial Area.median_c|c}}'],
        ['City centre', '{{q2.CBD.median_c|c}}'],
        ['Karura Forest and the Arboretum', '{{q2.cool_areas_median_c|c}}'],
      ],
      note: 'The Industrial Area\'s ground was {{q2.industrial_gap_c|c}} hotter than the forests.',
    },
  },
  {
    id: 'trees-nw', block: 'A', basemap: 'satellite', center: [36.79, -1.268], zoom: 11.6, mobileZoom: 10.8,
    // The three forests outlined and named, everything else dimmed (Stephane, 11 November 2026).
    layers: base([{ id: 's2-false', opacity: 1 }, { id: 'forest-mask', opacity: 1 }, { id: 'forests', opacity: 1 }]),
    chip: 'Sentinel-2, January to March 2026', legend: 's2-false',
    card: {
      title: 'The city\'s cool islands',
      // DRAFT 20 Nov (Claude), for Stephane to edit. Merges the false-colour "Where the trees are" step.
      text: 'In false colour, living plants show bright green and roofs and bare ground purple. These three forests are among the coolest ground in the county.',
      facts: [
        ['Karura Forest', '{{q5.parks.Karura Forest.park_median_c|c}} at the surface on hot mornings'],
        ['Nairobi Arboretum', '{{q5.parks.Nairobi Arboretum.park_median_c|c}}'],
        ['Ngong Road Forest', '{{x.copy_v3.forests.Ngong Road Forest.median_c|c}}'],
      ],
    },
  },
  {
    id: 'wards', block: 'A', basemap: 'satellite', center: COUNTY, zoom: 10.6, mobileZoom: 9.6,
    // Only the five hottest (red) and five coolest (blue) wards where people live; green is tree cover; the
    // other wards are dimmed and unnamed (Stephane, 11 November 2026).
    layers: base([{ id: 'ward-groups', opacity: 1 }, { id: 'trees', opacity: 0.95 }, { id: 'ward-dim', opacity: 1 },
      { id: 'wards-line', opacity: 1 }, { id: 'ward-labels', opacity: 1 }]),
    groups: { hot: HOT5, cool: COOL5 }, labelWards: [...HOT5, ...COOL5], top: ['trees'],
    labelText: 'census',   // ward labels carry the 2019 census count and the ward's area (D61)
    chip: 'January to March mornings, 2023 to 2026', legend: 'trees',
    legendTitle: 'Green: tree cover. Red: the five hottest wards where people live; blue: the five coolest',
    card: {
      title: 'Five hot wards, five cool wards',
      facts: [
        ['Five hottest wards, where people live', 'about {{x.wards_top5_census.hot.people_rounded|int}} people on {{x.wards_top5_census.hot.km2|d1}} km², tree cover {{x.wards_top5.hot_tree_pct|pct0}}'],
        ['Five coolest wards', 'about {{x.wards_top5_census.cool.people_rounded|int}} people on {{x.wards_top5_census.cool.km2|d1}} km², tree cover {{x.wards_top5.cool_tree_pct|pct0}}'],
      ],
      // 22 Nov: shortened to a summary (Stephane); the full comparison is on the Story page.
      note: 'People from the 2019 census.',
    },
  },

  // ---------------------------------------------------------------- Story block B: where children live and learn
  // Added 20 November 2026 for the Earthna and CIFF workshop (DECISIONS D59, D60). School dots are coloured by the
  // surface temperature within 100 m of each school (analysis/tables/schools_heat.csv), on the heat-diff scale.
    {
    id: 'people', block: 'B', basemap: 'satellite', center: [36.855, -1.285], zoom: 11.2, mobileZoom: 10.2,
    // Only the densest places are coloured, over the plain satellite image; the ten hottest wards where people
    // live are named (Stephane, 17 November 2026; replaces the dimmed map of 14 November).
    // 21 Nov (D61): only the crowded places on the hottest fifth, so the map shows the people the card counts.
    layers: base([{ id: 'population-hot', opacity: 0.9 }, { id: 'wards-line', opacity: 0.6 }, { id: 'ward-labels', opacity: 1 }]),
    labelWards: TOP10, quiet: true,
    chip: '2025 estimate, hot-season mornings 2023 to 2026', legend: 'population-hot',
    card: {
      title: 'Who lives on the hottest ground',
      facts: [
        ['People on the hottest fifth of the land', 'about {{q4.pop_in_hottest20|int}}'],
        ['Share of the county\'s people', '{{q4.pop_share_in_hottest20_pct|pct}}'],
        ['Hottest fifth means', 'surface above {{q4.hottest20_threshold_c|c}} on hot mornings'],
      ],
      note: 'Purple marks the crowded places on the hottest ground. Population: WorldPop 2025 estimate.',
    },
  },
  {
    id: 'rooftops', block: 'B', basemap: 'satellite', center: [36.9115, -1.2770], zoom: 15.2, mobileZoom: 14.6,
    layers: [{ id: 'buildings', opacity: 1 }, { id: 'ward-labels', opacity: 1 }],
    chip: 'January to March mornings, 2023 to 2026', legend: 'buildings',
    card: {
      title: 'Rooftops of Eastlands',
      // 21 Nov (D62): moved into the children's story, paired with Karen at the same scale.
      text: 'Rooftops in and around Kayole South, among the hottest places where people live.',
      facts: [
        ['Buildings in this view', '{{x.cover.views.eastlands.n_buildings|int}}, in and around {{x.cover.views.eastlands.ward|raw}}'],
        ['On ground hotter than the city median', '{{x.cover.views.eastlands.share_hotter_than_median_pct|pct}} of them'],
        ['Median surface temperature around them', '{{x.cover.views.eastlands.median_building_lst_c|c}}'],
      ],
      note: 'Each building shows the surface temperature of the 100 m around it.',
    },
  },
  {
    id: 'rooftops-karen', block: 'B', basemap: 'satellite', center: [36.75694, -1.36556], zoom: 15.2, mobileZoom: 14.6,
    layers: [{ id: 'buildings', opacity: 1 }, { id: 'ward-labels', opacity: 1 }],
    chip: 'January to March mornings, 2023 to 2026', legend: 'buildings',
    card: {
      title: 'Rooftops of Karen',
      // DRAFT 21 Nov (Claude), for Stephane to edit (D62).
      text: 'The same scale in Karen: houses stand apart among trees and gardens.',
      facts: [
        ['Buildings in this view', '{{x.cover.views.karen.n_buildings|int}}'],
        ['On ground hotter than the city median', '{{x.cover.views.karen.share_hotter_than_median_pct|pct}} of them'],
        ['Median surface temperature around them', '{{x.cover.views.karen.median_building_lst_c|c}}'],
      ],
    },
  },
  {
    id: 'schools', block: 'B', basemap: 'satellite', center: COUNTY, zoom: 10.6, mobileZoom: 9.6,
    layers: base([{ id: 'schools', opacity: 1 }]),
    chip: 'January to March mornings, 2023 to 2026', legend: 'heat-diff',
    legendTitle: 'Each dot is a school, coloured by the ground around it: difference from the city median, °C',
    card: {
      title: 'Where children go to school',
      // DRAFT 20 Nov (Claude), for Stephane to edit.
      text: 'Each dot is one of {{x.schools.n_schools|int}} schools, coloured by the heat of the ground around it on hot mornings.',
      facts: [
        ['Schools on the hotter half of the county\'s land', '{{x.schools.share_hotter_than_county_median_pct|pct}}'],
        ['Schools on the hottest fifth', '{{x.schools.n_on_hottest_fifth|int}}'],
      ],
    },
  },
  {
    id: 'schools-kangemi', block: 'B', basemap: 'satellite', center: [36.7526, -1.2690], zoom: 14.6, mobileZoom: 13.7,
    layers: [{ id: 'heat-diff', opacity: SAT_OP }, { id: 'wards-line', opacity: 1 }, { id: 'schools', opacity: 1 }],
    highlight: ['Kangemi'],
    chip: 'January to March mornings, 2023 to 2026', legend: 'heat-diff',
    card: {
      title: 'Kangemi, Nairobi\'s hottest ward where people live',
      // 22 Nov (Stephane): say plainly that Kangemi is the hottest ward, with its schools and children.
      text: '{{x.schools_trees_200m.by_ward.Kangemi.schools|int}} schools and about {{x.wards_top5_census.wards.Kangemi.school_age_2019|int}} school-age children (2019 census).',
      facts: [
        ['Schools on the hottest fifth of the county\'s land', '{{x.schools_trees_200m.by_ward.Kangemi.on_hottest_fifth|int}}'],
        ['Tree cover within 200 m of its schools (median)', '{{x.schools_trees_200m.by_ward.Kangemi.median_tree_pct_200m|pct}}'],
      ],
    },
  },
  {
    id: 'schools-viwandani', block: 'B', basemap: 'satellite', center: [36.8710, -1.3060], zoom: 13.8, mobileZoom: 12.9,
    layers: [{ id: 'heat-diff', opacity: SAT_OP }, { id: 'wards-line', opacity: 1 }, { id: 'schools', opacity: 1 }],
    highlight: ['Viwandani'],
    chip: 'January to March mornings, 2023 to 2026', legend: 'heat-diff',
    card: {
      title: 'Viwandani, the second hottest, beside the Industrial Area',
      // 22 Nov: what sets Viwandani apart. Its name means "at the factories"; it is part of the Mukuru settlements,
      // declared a Special Planning Area in 2017 for flooding and pollution (Wikipedia; Muungano wa Wanavijiji).
      text: 'Its name means "at the factories". {{x.schools_trees_200m.by_ward.Viwandani.schools|int}} schools and about {{x.wards_top5_census.wards.Viwandani.school_age_2019|int}} school-age children (2019 census).',
      facts: [
        ['Schools on the hottest fifth of the county\'s land', '{{x.schools_trees_200m.by_ward.Viwandani.on_hottest_fifth|int}}'],
        ['Tree cover within 200 m of its schools (median)', '{{x.schools_trees_200m.by_ward.Viwandani.median_tree_pct_200m|pct}}, the lowest of the wards shown'],
      ],
    },
  },
  {
    id: 'schools-karen', block: 'B', basemap: 'satellite', center: [36.7230, -1.3330], zoom: 12.4, mobileZoom: 11.5,
    layers: [{ id: 'heat-diff', opacity: SAT_OP }, { id: 'wards-line', opacity: 1 }, { id: 'schools', opacity: 1 }],
    highlight: ['Karen'],
    chip: 'January to March mornings, 2023 to 2026', legend: 'heat-diff',
    card: {
      title: 'Karen, Nairobi\'s coolest ward',
      text: '{{x.schools_trees_200m.by_ward.Karen.schools|int}} schools and about {{x.wards_top5_census.wards.Karen.school_age_2019|int}} school-age children (2019 census).',
      facts: [
        ['Schools on the hottest fifth of the county\'s land', '{{x.schools_trees_200m.by_ward.Karen.on_hottest_fifth|int}}'],
        ['Tree cover within 200 m of its schools (median)', '{{x.schools_trees_200m.by_ward.Karen.median_tree_pct_200m|pct}}'],
      ],
      link: ['#explore', 'Find the schools in your own ward below'],
    },
  },

  // ---------------------------------------------------------------- Story block C: a closer look (in "More on Nairobi's heat")
  {
    id: 'landcover', block: 'C', basemap: 'satellite', center: COUNTY, zoom: 10.3, mobileZoom: 9.4,
    layers: base([{ id: 'landcover', opacity: LIGHT_OP }]),
    chip: '2021', legend: 'landcover',
    card: {
      title: 'What covers the ground',
      text: 'In the dry months, open ground heated up as much as built-up land. Only trees and water were clearly cooler.',
      facts: [
        ['Built-up', '{{q3.by_name.built-up.share_pct|pct}} of the land, {{q3.by_name.built-up.median_c|c}}'],
        ['Grassland', '{{q3.by_name.grassland.share_pct|pct}}, {{q3.by_name.grassland.median_c|c}}'],
        ['Tree cover', '{{q3.by_name.tree.share_pct|pct}}, {{q3.by_name.tree.median_c|c}}'],
        ['Shrubland', '{{q3.by_name.shrubland.share_pct|pct}}, {{q3.by_name.shrubland.median_c|c}}'],
        ['Farmland', '{{q3.by_name.cropland.share_pct|pct}}, {{q3.by_name.cropland.median_c|c}}'],
        ['Bare ground', '{{q3.by_name.bare.share_pct|pct}}, {{q3.by_name.bare.median_c|c}}'],
      ],
      note: 'Median land surface temperature on clear January to March mornings, 2023 to 2026.',
    },
  },
  {
    id: 'cool', block: 'C', basemap: 'satellite', center: [36.840, -1.252], zoom: 13.3, mobileZoom: 12.3,
    layers: [{ id: 'places', opacity: 1 }],
    chip: 'Satellite image', legend: null,
    card: {
      title: 'Islands of cool',
      // DRAFT 16 Nov (Claude), for Stephane to edit.
      text: 'Karura Forest fills the top of this view. Along its edge the trees stop and roofs and roads begin; the next card shows how the ground temperature changes across that line.',
    },
  },
  {
    id: 'cool-heat', block: 'C', basemap: 'satellite', center: [36.840, -1.252], zoom: 13.3, mobileZoom: 12.3,
    layers: [{ id: 'heat-diff', opacity: SAT_OP }, { id: 'places', opacity: 1 }],
    chip: 'January to March mornings, 2023 to 2026', legend: 'heat-diff',
    card: {
      title: 'A little cooler near the forest',
      facts: [
        ['Built-up land within 100 m of Karura', '{{q5.parks.Karura Forest.ring_0_100_c|c}}'],
        ['Built-up land 700 to 1,000 m away', '{{q5.parks.Karura Forest.ring_700_1000_c|c}}'],
        ['The difference faded within', 'about {{q5.parks.Karura Forest.reach_m|int}} m'],
      ],
      note: 'This signal is small and the confidence is low to medium: read it as a hint, not a measured cooling distance.',
    },
  },
  {
    id: 'pair', block: 'C', basemap: 'satellite', center: [36.769, -1.274], zoom: 13.0, mobileZoom: 12.0,
    layers: [{ id: 'heat-diff', opacity: LIGHT_OP }, { id: 'wards-line', opacity: 1 }],
    highlight: ['Kileleshwa', 'Kawangware'],
    chip: 'January to March mornings, 2023 to 2026', legend: 'heat-diff',
    card: {
      title: 'Leafy and dense, a short walk apart',
      text: 'Kawangware, where about {{q9.Kawangware.pop_density_per_km2|int}} people live per square kilometre, had a median surface temperature of {{q9.Kawangware.lst_median_c|c}} on hot mornings and {{q9.Kawangware.tree_pct|pct0}} tree cover. Kileleshwa, {{q9.distance_km|d1}} km away at the nearest point, had {{q9.Kileleshwa.lst_median_c|c}} and {{q9.Kileleshwa.tree_pct|pct0}} tree cover.',
    },
  },
  {
    id: 'people-heat', block: 'C', basemap: 'satellite', center: [36.855, -1.285], zoom: 11.2, mobileZoom: 10.2,
    layers: base([{ id: 'heat-diff', opacity: LIGHT_OP }, { id: 'ward-dim', opacity: 1 }, { id: 'wards-line', opacity: 1 }, { id: 'ward-labels', opacity: 1 }]),
    groups: { hot: TOP10, cool: [] }, labelWards: TOP10, quiet: true,
    // The two averages are marked on the legend's colour bar (they are averages, not places on the map).
    legendMarkers: ['Ground under the average resident', 'Average for all county land'],
    chip: 'January to March mornings, 2023 to 2026', legend: 'heat-diff',
    card: {
      title: 'The same places, by surface temperature',
      facts: [
        ['Ground under the average resident', '{{q4.pop_weighted_county_lst_c|c}}'],
        ['Average for all county land', '{{q4.area_weighted_county_mean_c|c}}'],
      ],
    },
  },
  // A growing city, in two steps on the same colour scale so the 1990 and 2020 footprints can be compared
  // (Stephane, 11 November 2026). The county boundary is the same in both; the city filled in inside it.
  {
    id: 'growth', block: 'C', basemap: 'satellite', center: COUNTY, zoom: 10.3, mobileZoom: 9.4,
    layers: base([{ id: 'ghsl-1990', opacity: 0.9 }]),
    chip: '1990', legend: 'ghsl-1990', legendTitle: 'Built-up land in 1990',
    card: {
      title: 'Nairobi in 1990',
      text: 'In 1990, buildings covered about {{q6.built_km2.1990|km2}} of Nairobi County. The white line is the county boundary, which has not changed.',
      bars: [['1990', '{{q6.built_km2.1990|int}}', '{{q6.built_km2.2020|int}}', 'km² built up']],
    },
  },
  {
    id: 'growth-2020', block: 'C', basemap: 'satellite', center: COUNTY, zoom: 10.3, mobileZoom: 9.4,
    layers: base([{ id: 'ghsl-2020', opacity: 0.9 }]),
    chip: '2020', legend: 'ghsl-2020', legendTitle: 'Built-up land in 2020',
    card: {
      title: 'Nairobi in 2020',
      text: 'By 2020, buildings covered about {{q6.built_km2.2020|km2}}, around {{q6.built_ratio_2020_1990|d1}} times as much. The city did not spread past its boundary; it filled in the open land inside it.',
      bars: [['1990', '{{q6.built_km2.1990|int}}', '{{q6.built_km2.2020|int}}', 'km² built up'], ['2020', '{{q6.built_km2.2020|int}}', '{{q6.built_km2.2020|int}}', 'km² built up']],
    },
  },
];

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/** Card markup. Runs at build time in Node (vite.config.js) and is static HTML in the page. */
export function cardHTML(ch, i, n) {
  const c = ch.card;
  let h = `<article class="card" id="ch-${ch.id}" data-chapter="${ch.id}" aria-label="Map step ${i + 1} of ${n}: ${esc(c.title)}">`
    + `<h3 class="card__title">${esc(c.title)}</h3><div class="card__rule" aria-hidden="true"></div>`;
  if (c.text) h += `<p class="card__text">${esc(c.text)}</p>`;
  if (c.facts) h += `<ul class="card__facts">${c.facts.map(([k, v]) => `<li><strong>${esc(k)}:</strong> ${esc(v)}</li>`).join('')}</ul>`;
  if (c.bars) {
    h += `<div class="card__bars">${c.bars.map(([k, v, max, unit]) => `<div class="card__bar"><span class="card__bar-label">${esc(k)}</span>`
      + `<span class="card__bar-track"><span class="card__bar-fill" style="width: calc(${v} / ${max} * 100%)"></span></span>`
      + `<span class="card__bar-value">${esc(v)} ${esc(unit)}</span></div>`).join('')}</div>`;
  }
  if (c.note) h += `<p class="card__note">${esc(c.note)}</p>`;
  if (c.link) h += `<p class="card__link"><a href="${c.link[0]}">${esc(c.link[1])}</a></p>`;
  return `${h}</article>`;
}

export function blockHTML(block) {
  const list = CHAPTERS.filter((c) => c.block === block);
  return list.map((c, i) => `<div class="step">${cardHTML(c, i, list.length)}</div>`).join('\n');
}
