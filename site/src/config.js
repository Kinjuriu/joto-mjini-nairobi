// Shared paths, layer registry and the fixed colour ramps from prompts/03_story_site.md.

export const BASE = import.meta.env.BASE_URL;
export const abs = (path) => new URL(`${BASE}${path}`, window.location.href).href;
// For URL templates such as {fontstack}/{range}: `new URL` would percent-encode the braces.
export const absTemplate = (path) => `${new URL(BASE, window.location.href).href}${path}`;

export const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)');

export const HEAT = ['#FFF5E6', '#FDD9A8', '#F9B06A', '#EE7D3B', '#D2481E', '#A3200F', '#6B0F0A'];
export const LST_BREAKS = [24, 28, 32, 35, 38, 41, 44, 48];

const LANDSAT = 'Landsat: USGS';
const OSM = '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

// Raster layers are pre-coloured PMTiles made by src/analysis/web.py; legends come from data/legends.json.
export const RASTERS = {
  lst_hot_season: { file: 'data/lst_hot_season.pmtiles', attribution: LANDSAT },
  lst_cool_season: { file: 'data/lst_cool_season.pmtiles', attribution: LANDSAT },
  lst_anomaly: { file: 'data/lst_anomaly.pmtiles', attribution: LANDSAT },
  tree_fraction: { file: 'data/tree_fraction.pmtiles', attribution: 'Tree cover: ESA WorldCover 2021' },
  population: { file: 'data/population.pmtiles', attribution: 'Population: WorldPop 2025' },
  ghsl_built_1990: { file: 'data/ghsl_built_1990.pmtiles', attribution: 'Built-up: GHSL, EC JRC' },
  ghsl_built_2020: { file: 'data/ghsl_built_2020.pmtiles', attribution: 'Built-up: GHSL, EC JRC' },
};

export const ATTRIBUTION = `${OSM}, <a href="https://protomaps.com">Protomaps</a>`;

// MapLibre step expression that colours a numeric property with the surface temperature ramp.
export function heatStep(prop) {
  const expr = ['step', ['to-number', ['get', prop], 0], HEAT[0]];
  for (let i = 1; i < HEAT.length; i += 1) expr.push(LST_BREAKS[i], HEAT[i]);
  return expr;
}

export const fmtC = (v) => `${Number(v).toFixed(1)} °C`;
export const fmtSignedC = (v) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(Number(v)).toFixed(1)} °C`;
export const fmtInt = (v) => new Intl.NumberFormat('en-GB').format(Math.round(Number(v)));
export const fmtPct = (v) => `${Number(v).toFixed(1)} %`;

let cache = {};
export async function getJSON(path) {
  if (!cache[path]) cache[path] = fetch(abs(path)).then((r) => { if (!r.ok) throw new Error(`${path}: ${r.status}`); return r.json(); });
  return cache[path];
}

export async function countyBounds() {
  const gj = await getJSON('data/county.geojson');
  let [x0, y0, x1, y1] = [180, 90, -180, -90];
  const walk = (c) => { if (typeof c[0] === 'number') { x0 = Math.min(x0, c[0]); y0 = Math.min(y0, c[1]); x1 = Math.max(x1, c[0]); y1 = Math.max(y1, c[1]); } else c.forEach(walk); };
  gj.features.forEach((f) => walk(f.geometry.coordinates));
  return [[x0, y0], [x1, y1]];
}
