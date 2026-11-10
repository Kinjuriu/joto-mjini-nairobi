// QA: first screen and explorer at the widths in Stephane's pre-ship checklist.
import { chromium } from '@playwright/test';
const BASE = process.argv[2] || 'http://localhost:4173/joto-mjini/';
const OUT = process.argv[3] || '../outputs/screenshots';
const b = await chromium.launch();
const overflow = {};
for (const w of [360, 768, 1280, 1600]) {
  const p = await b.newPage({ viewport: { width: w, height: 900 } });
  await p.goto(BASE, { waitUntil: 'load' });
  await p.waitForTimeout(2500);
  await p.screenshot({ path: `${OUT}/width_${w}_first_screen.png` });
  overflow[w] = await p.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  await p.locator('#explore').scrollIntoViewIfNeeded();
  await p.waitForTimeout(2500);
  await p.screenshot({ path: `${OUT}/width_${w}_explorer.png` });
  await p.close();
}
console.log('horizontal overflow px by width', JSON.stringify(overflow));
await b.close();
