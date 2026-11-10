// Vite config for the Joto Mjini Nairobi story site.
//
// BASE is the one place to set the GitHub Pages project subpath. Override with SITE_BASE=/ for a root deploy.
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { defineConfig } from 'vite';

const BASE = process.env.SITE_BASE ?? '/joto-mjini-nairobi/';

// Every number in the copy is written as {{path|format}} and filled from analysis/results.json,
// the same file that analysis/FINDINGS.md is generated from. An unknown path fails the build.
const RESULTS = resolve(import.meta.dirname, '../analysis/results.json');
const CHAPTERS = resolve(import.meta.dirname, 'src/story/chapters.js');
// Extra results (animations, heatmap tables, roof check) are available to the copy as {{x.<path>}}.
const EXTRA = resolve(import.meta.dirname, '../analysis/results_extra.json');
const TOP_WARDS = resolve(import.meta.dirname, '../analysis/tables/top_wards.csv');

const nf = new Intl.NumberFormat('en-GB');
const FORMATS = {
  c: (v) => `${Number(v).toFixed(1)} °C`,          // temperature, one decimal, with unit
  absc: (v) => `${Math.abs(Number(v)).toFixed(1)} °C`,
  d1: (v) => Number(v).toFixed(1),                 // one decimal, no unit
  int: (v) => nf.format(Math.round(Number(v))),    // people counts, thousands separators
  pct: (v) => `${Number(v).toFixed(1)} %`,
  pct0: (v) => `${Math.round(Number(v))} %`,
  km2: (v) => `${Math.round(Number(v))} km²`,
  date: (v) => new Date(`${v}T00:00:00`).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }),
  raw: (v) => String(v),
};

function lookup(obj, path) {
  return path.split('.').reduce((o, k) => {
    if (o === undefined || o === null || !(k in Object(o))) throw new Error(`Unknown results path: ${path}`);
    return o[k];
  }, obj);
}

function topWardsTable() {
  const [head, ...rows] = readFileSync(TOP_WARDS, 'utf8').trim().split('\n');
  const cols = head.split(',');
  const recs = rows.map((r) => Object.fromEntries(r.split(',').map((v, i) => [cols[i], v])));
  const body = recs
    .map((r, i) => `<tr><td>${i + 1}</td><th scope="row">${r.ward_name}</th>`
      + `<td class="num">${FORMATS.c(r.pop_weighted_lst_c)}</td>`
      + `<td class="num">${FORMATS.int(Math.round(Number(r.pop_total) / 100) * 100)}</td>`
      + `<td class="num">${FORMATS.pct0(r.tree_pct)}</td></tr>`)
    .join('\n');
  return `<table class="data-table"><thead><tr><th scope="col">Rank</th><th scope="col">Ward</th>`
    + `<th scope="col" class="num">Surface temperature, people-weighted</th><th scope="col" class="num">People</th>`
    + `<th scope="col" class="num">Tree cover</th></tr></thead><tbody>${body}</tbody></table>`;
}

function findingsNumbers() {
  return {
    name: 'findings-numbers',
    transformIndexHtml: {
      order: 'pre',
      async handler(html) {
        const res = { ...JSON.parse(readFileSync(RESULTS, 'utf8')), x: JSON.parse(readFileSync(EXTRA, 'utf8')) };
        // Chapter cards are data in src/story/chapters.js; render them into the page first.
        if (html.includes('<!-- chapters:')) {
          const { blockHTML } = await import(`${pathToFileURL(CHAPTERS).href}?t=${Date.now()}`);
          html = html.replace(/<!-- chapters:([A-Z]) -->/g, (_, b) => blockHTML(b));
        }
        return html
          .replace(/\{\{table:top_wards\}\}/g, () => topWardsTable())
          .replace(/\{\{([^}|]+)(?:\|([a-z0-9]+))?\}\}/g, (_, path, fmt = 'raw') => {
            const f = FORMATS[fmt];
            if (!f) throw new Error(`Unknown format ${fmt} in {{${path}|${fmt}}}`);
            return f(lookup(res, path.trim()));
          });
      },
    },
  };
}

export default defineConfig({
  base: BASE,
  // Multi-page site: a missing file must 404, never fall back to index.html (tile requests depend on it).
  appType: 'mpa',
  plugins: [findingsNumbers()],
  build: {
    target: 'es2022', assetsInlineLimit: 0, chunkSizeWarningLimit: 2000,
    rollupOptions: {
      input: {
        main: resolve(import.meta.dirname, 'index.html'),
        layers: resolve(import.meta.dirname, 'layers.html'),
        slides: resolve(import.meta.dirname, 'slides.html'),
      },
    },
  },
  // The v1 site in _v1/ is kept for reference only; do not scan it for dependencies.
  optimizeDeps: { entries: ['index.html', 'layers.html', 'slides.html'] },
  server: { port: 5173 },
  preview: { port: 4173 },
});
