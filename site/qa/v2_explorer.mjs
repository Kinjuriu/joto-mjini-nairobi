// Explorer checks and screenshots (chunk 5): default view, ward chosen by keyboard, compare mode, building
// popup, phone bottom sheet, and restoring a shared link. Usage: node qa/v2_explorer.mjs
import { chromium } from '@playwright/test';
import { mkdirSync } from 'node:fs';

const BASE = process.env.URL || 'http://localhost:4173/joto-mjini-nairobi/';
const OUT = process.argv[2] || '../outputs/screenshots/v2/chunk5';
mkdirSync(OUT, { recursive: true });
const redact = (s) => s.replace(/access_token=[^&\s]+/g, 'access_token=REDACTED');
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const report = [];
const idle = (page, sel = 'ctl') => page.evaluate((s) => new Promise((r) => {
  const m = s === 'ctl' ? window.__explorer.ctl.map : window.__explorer.compare.right.map;
  if (m.loaded() && m.areTilesLoaded()) setTimeout(r, 400); else m.once('idle', () => setTimeout(r, 300));
  setTimeout(r, 10000);
}), sel);

async function open(ctxOpts, hash = '') {
  const ctx = await browser.newContext(ctxOpts);
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errs.push(redact(m.text()).slice(0, 160)); });
  page.on('response', (r) => { if (r.status() >= 400) errs.push(`HTTP ${r.status()} ${redact(r.url()).slice(0, 140)}`); });
  await page.goto(BASE + hash, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.getElementById('explore').scrollIntoView());
  await page.waitForFunction(() => window.__explorer, null, { timeout: 60000 });
  await idle(page);
  return { ctx, page, errs };
}

// Desktop
{
  const { ctx, page, errs } = await open({ viewport: { width: 1440, height: 900 } });
  await page.evaluate(() => document.querySelector('.explorer__body').scrollIntoView());
  await page.screenshot({ path: `${OUT}/01_default_1440.png` });
  // Ward by keyboard: focus the search box, type, arrow down, Enter.
  await page.focus('#ex-search');
  await page.keyboard.type('Kawang');
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('ArrowUp');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(1600);
  await idle(page);
  report.push(`ward chosen by keyboard: ${await page.evaluate(() => window.__explorer.state.ward)}; panel heading: ${await page.textContent('#ex-ward-body h3')}`);
  await page.screenshot({ path: `${OUT}/02_ward_selected_1440.png` });
  // Roof caveat ward.
  await page.evaluate(() => { const w = [...document.querySelectorAll('#ex-options li')]; return w; });
  await page.fill('#ex-search', 'Mabatini');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(1500);
  report.push(`roof caveat shown for Mabatini: ${await page.isVisible('.ward-panel__roof')}`);
  // Compare.
  await page.click('#ex-tab-layers');
  await page.click('.ex-tools button:has-text("Compare")');
  await page.waitForFunction(() => window.__explorer.compare, null, { timeout: 30000 });
  await page.evaluate(() => window.__explorer.ctl.map.jumpTo({ center: [36.86, -1.29], zoom: 10.4 }));
  await idle(page, 'cmp');
  await page.focus('.compare__handle');
  for (let i = 0; i < 5; i += 1) await page.keyboard.press('ArrowRight');
  report.push(`compare handle after 5 x ArrowRight: ${await page.getAttribute('.compare__handle', 'aria-valuenow')}`);
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${OUT}/03_compare_1440.png` });
  const shared = await page.evaluate(() => window.location.hash);
  report.push(`hash in compare mode: ${shared}`);
  await page.click('.ex-tools button:has-text("Close compare")');
  // Buildings on, zoom 15, click the centre for a popup.
  await page.check('#ex-cb-buildings');
  await page.evaluate(() => window.__explorer.ctl.map.jumpTo({ center: [36.9115, -1.2770], zoom: 15.3 }));
  await idle(page);
  const box = await page.locator('#ex-map').boundingBox();
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  await page.waitForTimeout(600);
  report.push(`building popup: ${(await page.locator('.mapboxgl-popup-content').textContent().catch(() => 'none'))?.slice(0, 120)}`);
  await page.screenshot({ path: `${OUT}/04_building_popup_1440.png` });
  // Year play button (then pause).
  await page.check('#ex-cb-ghsl');
  await page.click('.ex-play');
  await page.waitForTimeout(2800);
  await page.click('.ex-play');
  report.push(`built-up year after play: ${await page.inputValue('#ex-year')}`);
  report.push(`desktop errors: ${errs.length ? [...new Set(errs)].slice(0, 6).join(' | ') : 'none'}`);
  await ctx.close();
  // Restore the shared compare link in a new page.
  const r = await open({ viewport: { width: 1440, height: 900 } }, shared);
  await r.page.waitForFunction(() => window.__explorer.compare, null, { timeout: 30000 }).catch(() => {});
  report.push(`restored from link: compare=${await r.page.evaluate(() => !!window.__explorer.compare)}, ward=${await r.page.evaluate(() => window.__explorer.state.ward)}`);
  await r.ctx.close();
}
// Phone
{
  const { ctx, page, errs } = await open({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  await page.evaluate(() => document.querySelector('.explorer__body').scrollIntoView());
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${OUT}/05_phone_sheet_375.png` });
  await page.tap('#ex-search');
  await page.fill('#ex-search', 'Embakasi');
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${OUT}/06_phone_search_375.png` });
  await page.keyboard.press('Enter');
  await page.waitForTimeout(1500);
  await idle(page);
  await page.tap('.explorer__sheet-toggle');
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${OUT}/07_phone_ward_expanded_375.png` });
  await page.tap('.explorer__sheet-toggle');
  await page.tap('#ex-tab-layers');
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${OUT}/08_phone_layers_375.png` });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  report.push(`phone horizontal overflow: ${overflow}`);
  report.push(`phone errors: ${errs.length ? [...new Set(errs)].slice(0, 6).join(' | ') : 'none'}`);
  await ctx.close();
}
console.log(report.join('\n'));
await browser.close();
