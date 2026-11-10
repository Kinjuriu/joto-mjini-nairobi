// Screenshots of the interludes (chunk 4): animations beside text, heatmap tables, the highlighted chart and the
// calendar, at 1440 and 375 px; checks that videos pause off screen and that the table and chart answer keys.
import { chromium } from '@playwright/test';
import { mkdirSync } from 'node:fs';

const URL = process.env.URL || 'http://localhost:4173/joto-mjini-nairobi/';
const OUT = process.argv[2] || '../outputs/screenshots/v2/chunk4';
mkdirSync(OUT, { recursive: true });
const redact = (s) => s.replace(/access_token=[^&\s]+/g, 'access_token=REDACTED');
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const report = [];
const IDS = ['anim-mornings', 'landcover-table', 'season-compare', 'anim-growth', 'builtup-table', 'anim-day', 'air-chart', 'calendar'];
for (const [w, opts] of [['1440', { viewport: { width: 1440, height: 900 } }], ['375', { viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 }]]) {
  const ctx = await browser.newContext(opts);
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errs.push(redact(m.text()).slice(0, 160)); });
  page.on('response', (r) => { if (r.status() >= 400) errs.push(`HTTP ${r.status()} ${redact(r.url()).slice(0, 140)}`); });
  await page.goto(URL, { waitUntil: 'networkidle' });
  for (const id of IDS) {
    await page.evaluate((i) => document.getElementById(i).scrollIntoView({ block: 'start' }), id);
    await page.waitForTimeout(id.startsWith('anim') ? 2500 : 1500);
    if (id === 'season-compare') await page.waitForFunction(() => window.__compare, null, { timeout: 30000 }).catch(() => {});
    await page.waitForTimeout(id === 'season-compare' ? 4000 : 0);
    await page.screenshot({ path: `${OUT}/${id}_${w}.png` });
  }
  // Videos: playing on screen, paused off screen, button toggles.
  await page.evaluate(() => document.getElementById('anim-mornings').scrollIntoView({ block: 'center' }));
  await page.waitForTimeout(2500);
  const playing = await page.evaluate(() => !document.querySelector('#anim-mornings video').paused);
  await page.evaluate(() => document.getElementById('methods').scrollIntoView());
  await page.waitForTimeout(800);
  const pausedAway = await page.evaluate(() => document.querySelector('#anim-mornings video').paused);
  await page.evaluate(() => document.getElementById('anim-mornings').scrollIntoView({ block: 'center' }));
  await page.waitForTimeout(1500);
  await page.click('#anim-mornings .anim__btn');
  const pausedByButton = await page.evaluate(() => document.querySelector('#anim-mornings video').paused);
  report.push(`${w} video: playing on screen ${playing}, paused off screen ${pausedAway}, paused by button ${pausedByButton}`);
  // Keyboard on the built-up table and the chart.
  await page.focus('#builtup-table svg');
  await page.keyboard.press('ArrowRight');
  await page.keyboard.press('ArrowDown');
  report.push(`${w} table detail: ${await page.textContent('#builtup-table .chart-detail')}`);
  await page.focus('#air-chart svg');
  await page.keyboard.press('ArrowLeft');
  report.push(`${w} chart detail: ${await page.textContent('#air-chart .chart-detail')}`);
  report.push(`${w} errors: ${errs.length ? [...new Set(errs)].slice(0, 6).join(' | ') : 'none'}`);
  await ctx.close();
}
// Reduced motion: poster shown, video not playing until Play.
{
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
  const page = await ctx.newPage();
  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.getElementById('anim-mornings').scrollIntoView({ block: 'center' }));
  await page.waitForTimeout(2000);
  report.push(`reduced motion: video paused ${await page.evaluate(() => document.querySelector('#anim-mornings video').paused)}, button says ${await page.textContent('#anim-mornings .anim__btn')}`);
  await page.screenshot({ path: `${OUT}/anim-mornings_reduced-motion_1440.png` });
  await ctx.close();
}
console.log(report.join('\n'));
await browser.close();
