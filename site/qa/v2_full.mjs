// Chunk 6 checks: scroll slowly through the whole built page at 375 and 1440 px, record console errors, failed
// requests and missing tiles, count map instances; then record a walkthrough video at 1440 x 900.
// Usage: node qa/v2_full.mjs [checks|video|all]
import { chromium } from '@playwright/test';
import { mkdirSync, renameSync, readdirSync } from 'node:fs';

const URL = process.env.URL || 'http://localhost:4173/joto-mjini-nairobi/';
const what = process.argv[2] || 'all';
const redact = (s) => s.replace(/access_token=[^&\s]+/g, 'access_token=REDACTED');
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const out = [];

if (what !== 'video') {
  for (const [w, opts] of [['375', { viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 }], ['1440', { viewport: { width: 1440, height: 900 } }]]) {
    const ctx = await browser.newContext(opts);
    // Count Mapbox map instances by wrapping the WebGL context creation of map canvases.
    await ctx.addInitScript(() => { window.__canvases = 0; const o = HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext = function g(t, ...a) { if (/webgl/.test(t) && this.classList.contains('mapboxgl-canvas') && !this.__counted) { this.__counted = true; window.__canvases += 1; } return o.call(this, t, ...a); }; });
    const page = await ctx.newPage();
    const errs = []; const fails = []; const tiles404 = []; let tileReqs = 0; let mapboxReqs = 0;
    page.on('pageerror', (e) => errs.push(e.message));
    page.on('console', (m) => { if (m.type() === 'error') errs.push(redact(m.text()).slice(0, 180)); });
    page.on('requestfailed', (r) => { const f = r.failure()?.errorText || ''; if (!/ERR_ABORTED/.test(f)) fails.push(`${redact(r.url()).slice(0, 140)} ${f}`); });
    page.on('response', (r) => {
      const u = r.url();
      if (u.includes('/tiles/')) { tileReqs += 1; if (r.status() >= 400) tiles404.push(u.split('/tiles/')[1]); }
      if (u.includes('api.mapbox.com')) mapboxReqs += 1;
      if (r.status() >= 400 && !u.includes('/tiles/')) fails.push(`HTTP ${r.status()} ${redact(u).slice(0, 140)}`);
    });
    await page.goto(URL, { waitUntil: 'networkidle' });
    const H = await page.evaluate(() => document.documentElement.scrollHeight);
    const step = Math.round((opts.viewport.height) * 0.6);
    for (let y = 0; y < H; y += step) {
      await page.evaluate((yy) => window.scrollTo(0, yy), y);
      await page.waitForTimeout(700);
    }
    await page.waitForTimeout(2000);
    const maps = await page.evaluate(() => window.__canvases);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
    out.push(`${w}px: page height ${H}px; map instances created ${maps}; tile requests ${tileReqs}, tile 404s ${tiles404.length}${tiles404.length ? ` (${tiles404.slice(0, 5).join(', ')})` : ''}; Mapbox API requests ${mapboxReqs}; horizontal overflow ${overflow}`);
    out.push(`${w}px console errors: ${errs.length ? [...new Set(errs)].slice(0, 8).join(' | ') : 'none'}`);
    out.push(`${w}px failed requests: ${fails.length ? [...new Set(fails)].slice(0, 8).join(' | ') : 'none'}`);
    await ctx.close();
  }
  // Without JavaScript: the cards, tables' noscript notes and figures are present.
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, javaScriptEnabled: false });
  const page = await ctx.newPage();
  await page.goto(URL, { waitUntil: 'load' });
  out.push(`no JavaScript: ${await page.locator('.card').count()} cards in the page, ${await page.locator('img').count()} images, headline "${(await page.textContent('h1')).trim()}"`);
  await page.screenshot({ path: '../outputs/screenshots/v2/chunk6/no_js_1440.png', fullPage: false });
  await ctx.close();
}

if (what !== 'checks') {
  mkdirSync('../outputs/demo/_raw', { recursive: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, recordVideo: { dir: '../outputs/demo/_raw', size: { width: 1440, height: 900 } } });
  const page = await ctx.newPage();
  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);
  const ids = await page.evaluate(() => [...document.querySelectorAll('.card[data-chapter]')].map((c) => c.id));
  const smooth = async (to) => {
    const from = await page.evaluate(() => window.scrollY);
    const n = Math.max(8, Math.round(Math.abs(to - from) / 60));
    for (let i = 1; i <= n; i += 1) { await page.evaluate((y) => window.scrollTo(0, y), from + ((to - from) * i) / n); await page.waitForTimeout(40); }
  };
  for (const id of ids) {
    const y = await page.evaluate((cid) => { const r = document.getElementById(cid).getBoundingClientRect(); return window.scrollY + (r.top + r.bottom) / 2 - window.innerHeight / 2; }, id);
    await smooth(y);
    await page.waitForTimeout(4200);   // fly, fade and time to read
    if (id === 'ch-wards') break;
    if (id === 'ch-divide') {          // interlude 1 between the two blocks
      for (const sid of ['anim-mornings', 'landcover-table', 'season-compare']) {
        const yy = await page.evaluate((s) => window.scrollY + document.getElementById(s).getBoundingClientRect().top - 40, sid);
        await smooth(yy); await page.waitForTimeout(sid === 'anim-mornings' ? 8000 : 4500);
      }
    }
  }
  for (const sid of ['anim-growth', 'builtup-table', 'anim-day', 'air-chart']) {
    const yy = await page.evaluate((s) => window.scrollY + document.getElementById(s).getBoundingClientRect().top - 40, sid);
    await smooth(yy); await page.waitForTimeout(sid.startsWith('anim') ? 7000 : 4000);
  }
  const ye = await page.evaluate(() => window.scrollY + document.getElementById('explore').getBoundingClientRect().top);
  await smooth(ye);
  await page.waitForFunction(() => window.__explorer, null, { timeout: 60000 });
  await page.waitForTimeout(3000);
  for (const name of ['Viwandani', 'Kileleshwa']) {
    await page.click('#ex-search'); await page.fill('#ex-search', '');
    await page.keyboard.type(name, { delay: 90 });
    await page.waitForTimeout(500); await page.keyboard.press('Enter'); await page.waitForTimeout(5000);
  }
  await page.close();
  const v = await page.video().path();
  await ctx.close();
  renameSync(v, '../outputs/demo/joto-mjini-walkthrough.webm');
  out.push(`walkthrough video: outputs/demo/joto-mjini-walkthrough.webm (${readdirSync('../outputs/demo').join(', ')})`);
}
console.log(out.join('\n'));
await browser.close();
