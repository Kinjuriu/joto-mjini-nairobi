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
  // ---------------------------------------------------------------- Story block A: from space to heat
  {
    id: 'space', block: 'A', basemap: 'satellite', center: COUNTY, zoom: 10.3, mobileZoom: 9.4,
    layers: base([]),
    chip: 'Sentinel-2 cloudless, 2023', legend: null,
    card: {
      title: 'Nairobi from space',
      text: '[[COPY: one sentence on what the reader is looking at: Nairobi County in the dry season, seen by the Sentinel-2 satellites, with the county boundary in white]]',
    },
  },
  {
    id: 'trees', block: 'A', basemap: 'satellite', center: COUNTY, zoom: 10.3, mobileZoom: 9.4,
    layers: base([{ id: 's2-false', opacity: 1 }]),
    chip: 'Sentinel-2, January to March 2026', legend: 's2-false',
    card: {
      title: 'Where the trees are',
      text: 'This is false colour: the satellite also sees light our eyes cannot. Living plants show bright green. Roofs, roads and bare ground show purple.',
      facts: [['Ground mostly under trees', '{{q3.by_name.tree.share_pct|pct}} of the county']],
    },
  },
  {
    id: 'trees-nw', block: 'A', basemap: 'satellite', center: [36.79, -1.268], zoom: 11.6, mobileZoom: 10.8,
    // The three forests outlined and named, everything else dimmed (Stephane, 11 November 2026).
    layers: base([{ id: 's2-false', opacity: 1 }, { id: 'forest-mask', opacity: 1 }, { id: 'forests', opacity: 1 }]),
    chip: 'Sentinel-2, January to March 2026', legend: 's2-false',
    card: {
      title: 'Karura, the Arboretum and Ngong Road Forest',
      facts: [
        ['Karura Forest', '{{q5.parks.Karura Forest.park_median_c|c}} at the surface on hot mornings'],
        ['Nairobi Arboretum', '{{q5.parks.Nairobi Arboretum.park_median_c|c}}'],
        ['City Park', '{{q5.parks.City Park.park_median_c|c}}'],
        ['Half of the county\'s ground', 'hotter than {{q1.county_median_c|c}}'],
      ],
    },
  },
  {
    id: 'landcover', block: 'A', basemap: 'satellite', center: COUNTY, zoom: 10.3, mobileZoom: 9.4,
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
        ['Hottest ward', '{{q1.hottest_ward|raw}}, {{q1.hottest_ward_c|c}}'],
        ['Coolest ward', '{{q1.coolest_ward|raw}}, {{q1.coolest_ward_c|c}}'],
      ],
      note: 'Blue ground was cooler than the county median, orange and red hotter. Land surface temperature, not air temperature.',
    },
  },

  // ---------------------------------------------------------------- Story block B: a closer look
  {
    id: 'centre', block: 'B', basemap: 'satellite', center: [36.840, -1.296], zoom: 13.4, mobileZoom: 12.4,
    layers: [{ id: 'comparison-areas', opacity: 1 }],
    chip: 'Satellite image', legend: null,
    card: {
      title: 'City centre and Industrial Area',
      text: '[[COPY: introduce the two outlined areas: the Nairobi Central ward, and the Industrial Area as mapped in OpenStreetMap]]',
    },
  },
  {
    id: 'centre-heat', block: 'B', basemap: 'satellite', center: [36.840, -1.296], zoom: 13.4, mobileZoom: 12.4,
    layers: [{ id: 'heat-diff', opacity: SAT_OP }, { id: 'comparison-areas', opacity: 1 }],
    chip: 'January to March mornings, 2023 to 2026', legend: 'heat-diff',
    card: {
      title: 'The same view, by surface temperature',
      facts: [
        ['City centre', '{{q2.CBD.median_c|c}}'],
        ['Industrial Area', '{{q2.Industrial Area.median_c|c}}'],
        ['Karura Forest and the Arboretum', '{{q2.cool_areas_median_c|c}}'],
        ['Difference', '{{q2.gap_c|c}}'],
      ],
      note: 'On hot mornings, the ground in the city centre and Industrial Area ({{q2.hot_areas_median_c|c}}) was {{q2.gap_c|c}} hotter than Karura Forest and the Nairobi Arboretum ({{q2.cool_areas_median_c|c}}).',
    },
  },
  {
    id: 'rooftops', block: 'B', basemap: 'satellite', center: [36.9115, -1.2770], zoom: 15.2, mobileZoom: 14.6,
    layers: [{ id: 'buildings', opacity: 1 }, { id: 'ward-labels', opacity: 1 }],
    chip: 'January to March mornings, 2023 to 2026', legend: 'buildings',
    card: {
      title: 'Rooftops of Eastlands',
      text: 'Weighted by where people live, the hottest wards include Kayole South, Dandora Area I and Kariobangi North.',
      facts: [
        ['Ten hottest wards by where people live', 'home to about {{q4.top10_total_pop|int}} people'],
        ['Most tree cover in any of them', '{{q4.top10_max_tree_pct|pct}} of the land'],
      ],
      note: 'Each building shows the surface temperature of the area of about 100 m around it. Bare iron sheet roofs give off heat less efficiently, so where they cover much of the ground the satellite can read the surface as cooler than it is. Treat the surface temperature of these wards as a lower bound.',
    },
  },
  {
    id: 'cool', block: 'B', basemap: 'satellite', center: [36.840, -1.252], zoom: 13.3, mobileZoom: 12.3,
    layers: [{ id: 'places', opacity: 1 }],
    chip: 'Satellite image', legend: null,
    card: {
      title: 'Islands of cool',
      text: '[[COPY: point out the edge of Karura Forest and the built-up land beside it]]',
    },
  },
  {
    id: 'cool-heat', block: 'B', basemap: 'satellite', center: [36.840, -1.252], zoom: 13.3, mobileZoom: 12.3,
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
    id: 'pair', block: 'B', basemap: 'satellite', center: [36.769, -1.274], zoom: 13.0, mobileZoom: 12.0,
    layers: [{ id: 'heat-diff', opacity: LIGHT_OP }, { id: 'wards-line', opacity: 1 }],
    highlight: ['Kileleshwa', 'Kawangware'],
    chip: 'January to March mornings, 2023 to 2026', legend: 'heat-diff',
    card: {
      title: 'Leafy and dense, a short walk apart',
      text: 'Kawangware, where about {{q9.Kawangware.pop_density_per_km2|int}} people live per square kilometre, had a median surface temperature of {{q9.Kawangware.lst_median_c|c}} on hot mornings and {{q9.Kawangware.tree_pct|pct0}} tree cover. Kileleshwa, {{q9.distance_km|d1}} km away at the nearest point, had {{q9.Kileleshwa.lst_median_c|c}} and {{q9.Kileleshwa.tree_pct|pct0}} tree cover.',
    },
  },
  {
    id: 'people', block: 'B', basemap: 'satellite', center: [36.855, -1.285], zoom: 11.2, mobileZoom: 10.2,
    layers: base([{ id: 'population', opacity: LIGHT_OP }, { id: 'ward-labels', opacity: 1 }]),
    labelWards: TOP10,
    chip: '2025 estimate', legend: 'population',
    card: {
      title: 'Who lives on the hottest ground',
      facts: [
        ['People on the hottest fifth of the land', 'about {{q4.pop_in_hottest20|int}}'],
        ['Share of the county\'s people', '{{q4.pop_share_in_hottest20_pct|pct}}'],
        ['Hottest fifth means', 'surface above {{q4.hottest20_threshold_c|c}} on hot mornings'],
      ],
      note: 'Population from WorldPop 2025, a modelled estimate that may undercount the densest settlements.',
    },
  },
  {
    id: 'people-heat', block: 'B', basemap: 'satellite', center: [36.855, -1.285], zoom: 11.2, mobileZoom: 10.2,
    layers: base([{ id: 'heat-diff', opacity: LIGHT_OP }, { id: 'ward-labels', opacity: 1 }]),
    labelWards: TOP10,
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
    id: 'growth', block: 'B', basemap: 'satellite', center: COUNTY, zoom: 10.3, mobileZoom: 9.4,
    layers: base([{ id: 'ghsl-1990', opacity: 0.9 }]),
    chip: '1990', legend: 'ghsl-1990', legendTitle: 'Built-up land in 1990',
    card: {
      title: 'Nairobi in 1990',
      text: 'In 1990, buildings covered about {{q6.built_km2.1990|km2}} of Nairobi County. The white line is the county boundary, which has not changed.',
      bars: [['1990', '{{q6.built_km2.1990|int}}', '{{q6.built_km2.2020|int}}', 'km² built up']],
    },
  },
  {
    id: 'growth-2020', block: 'B', basemap: 'satellite', center: COUNTY, zoom: 10.3, mobileZoom: 9.4,
    layers: base([{ id: 'ghsl-2020', opacity: 0.9 }]),
    chip: '2020', legend: 'ghsl-2020', legendTitle: 'Built-up land in 2020',
    card: {
      title: 'Nairobi in 2020',
      text: 'By 2020, buildings covered about {{q6.built_km2.2020|km2}}, around {{q6.built_ratio_2020_1990|d1}} times as much. The city did not spread past its boundary; it filled in the open land inside it.',
      bars: [['1990', '{{q6.built_km2.1990|int}}', '{{q6.built_km2.2020|int}}', 'km² built up'], ['2020', '{{q6.built_km2.2020|int}}', '{{q6.built_km2.2020|int}}', 'km² built up']],
    },
  },
  {
    id: 'wards', block: 'B', basemap: 'satellite', center: COUNTY, zoom: 10.6, mobileZoom: 9.6,
    // Only the five hottest (red) and five coolest (blue) wards where people live; green is tree cover; the
    // other wards are dimmed and unnamed (Stephane, 11 November 2026).
    layers: base([{ id: 'ward-groups', opacity: 1 }, { id: 'trees', opacity: 0.95 }, { id: 'ward-dim', opacity: 1 },
      { id: 'wards-line', opacity: 1 }, { id: 'ward-labels', opacity: 1 }]),
    groups: { hot: HOT5, cool: COOL5 }, labelWards: [...HOT5, ...COOL5], top: ['trees'],
    chip: 'January to March mornings, 2023 to 2026', legend: 'trees',
    legendTitle: 'Green: tree cover. Red: the five hottest wards where people live; blue: the five coolest',
    card: {
      title: 'Five hot wards, five cool wards',
      facts: [
        ['Five hottest wards, where people live', '{{x.wards_top5.hot_lst_c|c}}, tree cover {{x.wards_top5.hot_tree_pct|pct0}}'],
        ['Five coolest wards', '{{x.wards_top5.cool_lst_c|c}}, tree cover {{x.wards_top5.cool_tree_pct|pct0}}'],
        ['Difference', '{{x.wards_top5.gap_c|c}}'],
      ],
      note: 'Red outlines: Kangemi, Viwandani, Kabiro, Dandora Area I, Baba Dogo. Blue: Kileleshwa, Mutu-ini, Karura, Kitisuru, Karen.',
      link: ['#explore', 'Find your own ward below'],
    },
  },
];

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/** Card markup. Runs at build time in Node (vite.config.js) and is static HTML in the page. */
export function cardHTML(ch, i, n) {
  const c = ch.card;
  let h = `<article class="card" id="ch-${ch.id}" data-chapter="${ch.id}" aria-label="Map step ${i + 1} of ${n}: ${esc(c.title)}">`
    + `<div class="card__rule" aria-hidden="true"></div><h3 class="card__title">${esc(c.title)}</h3>`;
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
