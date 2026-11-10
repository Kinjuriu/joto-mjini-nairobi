// Smoke test: load a page, report console errors and failed requests, save one screenshot.
import { chromium } from '@playwright/test';
const [url, out, w = '1440', h = '900'] = process.argv.slice(2);
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: +w, height: +h } });
const errs = [];
page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') errs.push(`${m.type()}: ${m.text()}`); });
page.on('pageerror', (e) => errs.push(`pageerror: ${e.message}`));
page.on('requestfailed', (r) => errs.push(`failed: ${r.url()} ${r.failure()?.errorText}`));
page.on('response', (r) => { if (r.status() >= 400) errs.push(`HTTP ${r.status()}: ${r.url()}`); });
await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForTimeout(2500);
await page.screenshot({ path: out });
console.log(errs.slice(0, 30).join('\n') || 'no errors');
await browser.close();
