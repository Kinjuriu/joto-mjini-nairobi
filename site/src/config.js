// Shared paths, formatting and the fixed colour ramps from prompts/v2/DESIGN_BRIEF_v2.md.

export const BASE = import.meta.env.BASE_URL;
export const abs = (path) => new URL(`${BASE}${path}`, window.location.href).href;
// For URL templates such as {z}/{x}/{y}: `new URL` would percent-encode the braces.
export const absTemplate = (path) => `${new URL(BASE, window.location.href).href}${path}`;

export const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';
// Imagery for the "Satellite" basemap: 'sentinel2' (our own composite under Mapbox roads and labels; the
// default while Mapbox refuses satellite tiles for this token, DECISIONS D33), 'mapbox' (Satellite Streets),
// or 'auto' (probe one Mapbox satellite tile per session). Set VITE_SATELLITE in site/.env.local.
export const SATELLITE = import.meta.env.VITE_SATELLITE || 'auto';
export const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)');

// Difference from the city median (°C): the default heat view.
export const DIFF_BREAKS = [-6, -4, -2, -0.5, 0.5, 2, 4, 6];
export const DIFF_COLOURS = ['#1D4E6F', '#3B7CA6', '#8DBAD6', '#C9DDE9', '#F2EFE9', '#F6CBA6', '#F4A26B', '#D9542B', '#A1201A'];
export const ACCENT = '#1D4E6F';

/** Mapbox step expression colouring a numeric value with the diverging ramp. */
export function diffStep(valueExpr) {
  const expr = ['step', valueExpr, DIFF_COLOURS[0]];
  DIFF_BREAKS.forEach((b, i) => expr.push(b, DIFF_COLOURS[i + 1]));
  return expr;
}

export const fmtC = (v) => `${Number(v).toFixed(1)} °C`;
export const fmtSignedC = (v) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(Number(v)).toFixed(1)} °C`;
export const fmtInt = (v) => new Intl.NumberFormat('en-GB').format(Math.round(Number(v)));
export const fmtPct = (v) => `${Number(v).toFixed(1)} %`;
export const fmtPct0 = (v) => `${Math.round(Number(v))} %`;
export const ordinal = (n) => {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return `${n}${s[(v - 20) % 10] || s[v] || s[0]}`;
};

const cache = {};
export async function getJSON(path) {
  if (!cache[path]) cache[path] = fetch(abs(path)).then((r) => { if (!r.ok) throw new Error(`${path}: ${r.status}`); return r.json(); });
  return cache[path];
}

/** The layer manifest written by src/web/tiles.py: tiles, zooms, legends, sources and date chips. */
export const getManifest = () => getJSON('tiles/manifest.json').then((m) => m.layers);
