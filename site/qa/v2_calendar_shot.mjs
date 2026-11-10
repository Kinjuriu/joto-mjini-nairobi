// Screenshot the lower part of the calendar (El Niño bracket and key) and the ward cover table at 1440 px.
import { chromium } from '@playwright/test';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
await p.goto('http://localhost:4173/joto-mjini-nairobi/', { waitUntil: 'networkidle' });
await p.evaluate(() => document.getElementById('calendar').scrollIntoView({ block: 'end' }));
await p.waitForTimeout(2000);
await p.evaluate(() => document.getElementById('calendar').scrollIntoView({ block: 'end' }));
await p.waitForTimeout(1000);
console.log(await p.evaluate(() => `bracket labels: ${[...document.querySelectorAll('.heatmap__bracket-label')].map((t) => t.textContent).join(' ')}; key items: ${document.querySelectorAll('.calendar-key li').length}`));
await p.screenshot({ path: '../outputs/screenshots/v2/chunk4/calendar_bottom_1440.png' });
await p.evaluate(() => document.getElementById('landcover-table').scrollIntoView({ block: 'center' }));
await p.waitForTimeout(2000);
await p.screenshot({ path: '../outputs/screenshots/v2/chunk4/landcover-table_1440.png' });
await b.close();
