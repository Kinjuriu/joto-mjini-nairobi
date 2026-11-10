// Screenshot every story chapter at 1440 and 375 px, and check that the chapter on the map matches the card
// in the middle of the screen. Usage: node qa/v2_story.mjs [1440|375|both] [outdir]
import { chromium } from '@playwright/test';
import { mkdirSync } from 'node:fs';

const URL = process.env.URL || 'http://localhost:4173/joto-mjini-nairobi/';
const which = process.argv[2] || 'both';
const OUT = process.argv[3] || '../outputs/screenshots/v2/chunk3';
mkdirSync(OUT, { recursive: true });
const redact = (s) => s.replace(/access_token=[^&\s]+/g, 'access_token=REDACTED');
const sizes = { 1440: { width: 1440, height: 900 }, 375: { width: 375, height: 812, isMobile: true, hasTouch: true, deviceScaleFactor: 2 } };
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const report = [];
for (const w of which === 'both' ? ['1440', '375'] : [which]) {
  const { width, height, ...rest } = sizes[w];
  const ctx = await browser.newContext({ viewport: { width, height }, ...rest });
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errs.push(redact(m.text()).slice(0, 200)); });
  page.on('response', (r) => { if (r.status() >= 400) errs.push(`HTTP ${r.status()} ${redact(r.url()).slice(0, 160)}`); });
  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.screenshot({ path: `${OUT}/00_intro_${w}.png` });
  await page.evaluate(() => document.querySelector('.story[data-block="A"]').scrollIntoView());
  await page.waitForFunction(() => window.__story && window.__story.chapter, null, { timeout: 60000 });
  const ids = await page.evaluate(() => window.__story.chapters.map((c) => c.id));
  for (const [n, id] of ids.entries()) {
    await page.evaluate((cid) => {
      const c = document.getElementById(`ch-${cid}`);
      const r = c.getBoundingClientRect();
      window.scrollBy(0, (r.top + r.bottom) / 2 - window.innerHeight * (window.innerWidth < 768 ? 0.72 : 0.5));
    }, id);
    await page.waitForFunction((cid) => window.__story.chapter === cid, id, { timeout: 30000 }).catch(() => {});
    await page.waitForTimeout(2300);
    await page.evaluate(() => new Promise((r) => { const m = window.__story.ctl.map; if (m.areTilesLoaded()) r(); else m.once('idle', r); setTimeout(r, 8000); }));
    const on = await page.evaluate(() => window.__story.chapter);
    report.push(`${w} ${id}: map shows ${on}${on === id ? '' : '  <-- MISMATCH'}`);
    await page.screenshot({ path: `${OUT}/${String(n + 1).padStart(2, '0')}_${id}_${w}.png` });
  }
  // Fast jump: End key, then back to the top of block B, and check the applied chapter.
  await page.keyboard.press('End');
  await page.waitForTimeout(800);
  await page.evaluate(() => document.querySelector('.story[data-block="B"]').scrollIntoView());
  await page.waitForTimeout(1500);
  report.push(`${w} after End then jump to block B: map shows ${await page.evaluate(() => window.__story.chapter)}`);
  report.push(`${w} errors: ${errs.length ? [...new Set(errs)].slice(0, 8).join(' | ') : 'none'}`);
  await ctx.close();
}
console.log(report.join('\n'));
await browser.close();
