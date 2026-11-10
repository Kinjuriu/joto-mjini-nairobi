// Widths check (chunk 6): at 360, 768, 1280 and 1600 px, visit each section and record horizontal overflow and
// errors, with a screenshot of the story and the explorer.
import { chromium } from '@playwright/test';
const URL = process.env.URL || 'http://localhost:4173/joto-mjini-nairobi/';
const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
for (const w of [360, 768, 1280, 1600]) {
  const p = await b.newPage({ viewport: { width: w, height: w < 768 ? 780 : 900 } });
  const errs = [];
  p.on('pageerror', (e) => errs.push(e.message));
  p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().replace(/access_token=[^&\s]+/g, 'X').slice(0, 120)); });
  await p.goto(URL, { waitUntil: 'networkidle' });
  let over = [];
  for (const id of ['ch-divide', 'anim-mornings', 'landcover-table', 'season-compare', 'ch-pair', 'builtup-table', 'calendar', 'explore', 'methods']) {
    await p.evaluate((i) => document.getElementById(i).scrollIntoView({ block: 'center' }), id);
    await p.waitForTimeout(1500);
    if (await p.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1)) over.push(id);
    if (id === 'ch-pair') await p.screenshot({ path: `../outputs/screenshots/v2/chunk6/story_pair_${w}.png` });
    if (id === 'explore') { await p.waitForTimeout(3000); await p.screenshot({ path: `../outputs/screenshots/v2/chunk6/explorer_${w}.png` }); }
  }
  console.log(`${w}px: overflow at ${over.join(', ') || 'none'}; errors ${errs.length ? [...new Set(errs)].join(' | ') : 'none'}`);
  await p.close();
}
await b.close();
