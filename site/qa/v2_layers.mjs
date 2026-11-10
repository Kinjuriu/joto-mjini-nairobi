// Screenshots of every layer on the layer test page at zooms 10, 12 and 14 (1440 px wide),
// plus the basemap tests (heat over each candidate basemap). Usage: node qa/v2_layers.mjs [layers|basemaps|all]
import { chromium } from '@playwright/test';
import { mkdirSync } from 'node:fs';

const URL = process.env.URL || 'http://localhost:4173/joto-mjini-nairobi/layers.html';
const OUT = '../outputs/screenshots/v2';
const what = process.argv[2] || 'all';
const only = process.argv[3] ? process.argv[3].split(',') : null;   // optional subset of layer ids
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errs = [];
page.on('pageerror', (e) => errs.push(e.message));
page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().replace(/access_token=[^&\s]+/g, 'access_token=REDACTED')); });
const redact = (u) => u.replace(/access_token=[^&]+/, 'access_token=REDACTED');
page.on('response', (r) => { if (r.status() >= 400) errs.push(`HTTP ${r.status()} ${redact(r.url())}`); });
await page.goto(URL, { waitUntil: 'networkidle' });
await page.waitForFunction(() => window.__layers);
const set = (o) => page.evaluate((x) => window.__layers.set(x), o);
const shot = async (dir, name) => { mkdirSync(`${OUT}/${dir}`, { recursive: true }); await page.waitForTimeout(400); await page.screenshot({ path: `${OUT}/${dir}/${name}.png` }); };

// Each layer: whole city at z10, city centre at z12, Eastlands at z14 (Karura for trees and S2 false colour).
const LAYERS = {
  'heat-diff': 'light', 'heat-abs': 'light', 'heat-hottest-day': 'light', 'heat-cool-season': 'light',
  landcover: 'light', trees: 'satellite', population: 'light', 'growth-1990-2020': 'light',
  'ghsl-1990': 'light', 'ghsl-2020': 'light', 's2-true': 'light', 's2-false': 'light',
};
if (what === 'all' || what === 'layers') {
  const ids = await page.evaluate(() => Object.keys(window.__layers.ctl.manifest));
  for (const [id, bm] of Object.entries(LAYERS)) {
    if (!ids.includes(id)) { console.log(`skip ${id} (not in manifest)`); continue; }
    if (only && !only.includes(id)) continue;
    const op = bm === 'satellite' ? 0.75 : (id.startsWith('s2') ? 1 : 0.9);
    const zv = id === 'trees' || id === 's2-false' ? 'karura' : 'eastlands';
    for (const [view, z] of [['cbd', 10], ['cbd', 12], [zv, 14]]) {
      await set({ basemap: bm, raster: id, overlays: ['county-line', 'ward-labels'], opacity: op, view, zoom: z });
      await shot('chunk2', `${id}_z${z}`);
    }
  }
  await set({ basemap: 'satellite', raster: 'heat-diff', overlays: ['county-line', 'ward-labels', 'buildings'], opacity: 0, view: 'eastlands', zoom: 15 });
  await shot('chunk2', 'buildings_z15_satellite');
  await set({ basemap: 'light', raster: 'heat-diff', overlays: ['county-line', 'wards-fill', 'wards-line', 'ward-labels'], opacity: 0, view: 'cbd', zoom: 11 });
  await shot('chunk2', 'wards-fill_z11');
}
if (what === 'all' || what === 'basemaps') {
  for (const bm of ['light', 'satellite', 'dark']) {
    for (const [z, view] of [[10, 'cbd'], [12, 'cbd'], [14, 'eastlands']]) {
      for (const op of bm === 'satellite' ? [0.75, 0.9] : [0.9]) {
        await set({ basemap: bm, raster: 'heat-diff', overlays: ['county-line', 'ward-labels'], opacity: op, view, zoom: z });
        await shot('basemap_tests', `heat-diff_${bm}_op${Math.round(op * 100)}_z${z}`);
      }
    }
  }
}
console.log(errs.length ? errs.slice(0, 20).join('\n') : 'no errors');
await browser.close();
