// QA: screenshots, console errors and failed requests for the built site served by `npx vite preview`.
// Usage: node qa/shoot.mjs [baseUrl] [outDir] [--quick]
import { chromium } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'node:fs';

const BASE = process.argv[2] || 'http://localhost:4173/joto-mjini/';
const OUT = process.argv[3] || '../outputs/screenshots';
const QUICK = process.argv.includes('--quick');
mkdirSync(OUT, { recursive: true });

const report = { console: [], failed: [], pageErrors: [], ranges: [] };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function open(browser, width, height, opts = {}) {
  const ctx = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: width < 500 ? 2 : 1, ...opts });
  const page = await ctx.newPage();
  page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) report.console.push(`[${width}] ${m.type()}: ${m.text()}`); });
  page.on('pageerror', (e) => report.pageErrors.push(`[${width}] ${e.message}`));
  page.on('requestfailed', (r) => report.failed.push(`[${width}] ${r.url()} ${r.failure()?.errorText}`));
  page.on('response', (r) => {
    if (r.status() >= 400) report.failed.push(`[${width}] HTTP ${r.status()} ${r.url()}`);
    if (r.url().endsWith('.pmtiles') && report.ranges.length < 40) report.ranges.push(`${r.status()} ${r.request().headers().range || 'no range'} ${r.url().split('/').pop()}`);
  });
  return { ctx, page };
}

async function scrollThrough(page) {
  const h = await page.evaluate(() => document.documentElement.scrollHeight);
  for (let y = 0; y < h; y += 500) { await page.evaluate((yy) => window.scrollTo(0, yy), y); await sleep(120); }
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(800);
}

const browser = await chromium.launch();
for (const [w, h] of [[1440, 900], [375, 812]]) {
  const { ctx, page } = await open(browser, w, h);
  await page.goto(BASE, { waitUntil: 'load' });
  await sleep(2500);
  await page.screenshot({ path: `${OUT}/first_screen_${w}.png` });
  if (QUICK) { await ctx.close(); continue; }
  await scrollThrough(page);
  await sleep(1500);
  await page.screenshot({ path: `${OUT}/full_page_${w}.png`, fullPage: true });

  // Each scrollytelling chapter.
  const steps = await page.$$('.step');
  for (let i = 0; i < steps.length; i += 1) {
    await steps[i].scrollIntoViewIfNeeded();
    await page.evaluate((idx) => {
      const s = document.querySelectorAll('.step')[idx];
      const r = s.getBoundingClientRect();
      window.scrollBy(0, r.top - window.innerHeight * 0.35);
    }, i);
    await sleep(2600);
    await page.screenshot({ path: `${OUT}/chapter_${i + 1}_${w}.png` });
  }

  // Explorer with one ward selected.
  await page.locator('#explore').scrollIntoViewIfNeeded();
  await sleep(1500);
  await page.fill('#ward-input', 'Viwand');
  await page.keyboard.press('Enter');
  await sleep(2500);
  await page.locator('.explorer__layout').scrollIntoViewIfNeeded();
  await page.screenshot({ path: `${OUT}/explorer_ward_${w}.png` });
  await page.click('[data-layer="buildings"]');
  await sleep(3000);
  await page.screenshot({ path: `${OUT}/explorer_buildings_${w}.png` });
  report.hash = await page.evaluate(() => window.location.hash);

  // Hero swipe by keyboard.
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(800);
  await page.focus('#hero .compare__handle');
  for (let k = 0; k < 10; k += 1) await page.keyboard.press('ArrowLeft');
  await sleep(600);
  await page.screenshot({ path: `${OUT}/hero_swiped_${w}.png` });
  report[`handle_${w}`] = await page.$eval('#hero .compare__handle', (e) => e.getAttribute('aria-valuenow'));
  await ctx.close();
}

if (!QUICK) {
  // JavaScript off.
  const { ctx, page } = await open(browser, 1440, 900, { javaScriptEnabled: false });
  await page.goto(BASE, { waitUntil: 'load' });
  await page.screenshot({ path: `${OUT}/no_javascript_1440.png`, fullPage: true });
  await ctx.close();
  // Reduced motion.
  const rm = await open(browser, 1440, 900, { reducedMotion: 'reduce' });
  await rm.page.goto(BASE, { waitUntil: 'load' });
  await scrollThrough(rm.page);
  await rm.ctx.close();
  // Page weight before map tiles: everything except .pmtiles and tile data.
  const pw = await open(browser, 1440, 900);
  let bytes = 0;
  pw.page.on('response', async (r) => {
    if (r.url().includes('.pmtiles')) return;
    try { bytes += (await r.body()).length; } catch { /* ignore */ }
  });
  await pw.page.goto(BASE, { waitUntil: 'load' });
  await sleep(2000);
  report.first_load_bytes_excluding_tiles = bytes;
  await pw.ctx.close();
}
await browser.close();
writeFileSync(`${OUT}/qa_report.json`, JSON.stringify(report, null, 2));
console.log(JSON.stringify({ console: report.console.slice(0, 20), pageErrors: report.pageErrors, failed: report.failed.slice(0, 20), ranges: report.ranges.slice(0, 5), hash: report.hash, h1440: report.handle_1440, h375: report.handle_375, bytes: report.first_load_bytes_excluding_tiles }, null, 2));
