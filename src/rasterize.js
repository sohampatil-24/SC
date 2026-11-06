// Rasterize logo SVGs to PNG (transparent + white-background versions).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const dir = path.join(__dirname, '..', 'logo');
const jobs = [
  ['unique-logo-horizontal.svg', 'unique-logo-horizontal.png', null, 2],
  ['unique-logo-horizontal.svg', 'unique-logo-horizontal-on-white.png', '#ffffff', 2],
  ['unique-logo-horizontal-white.svg', 'unique-logo-horizontal-white.png', null, 2],
  ['unique-logo-stacked.svg', 'unique-logo-stacked.png', null, 2],
  ['unique-logo-stacked.svg', 'unique-logo-stacked-on-white.png', '#ffffff', 2],
  ['unique-logo-icon.svg', 'unique-logo-icon.png', null, 2],
];

(async () => {
  const browser = await chromium.launch();
  for (const [src, out, bg, scale] of jobs) {
    const svg = fs.readFileSync(path.join(dir, src), 'utf8');
    const m = svg.match(/viewBox="0 0 (\d+) (\d+)"/);
    const w = +m[1], h = +m[2];
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: scale });
    const pad = bg ? 0 : 0;
    await page.setContent(`<html><body style="margin:0;background:${bg || 'transparent'}">${svg}</body></html>`);
    await page.screenshot({ path: path.join(dir, out), omitBackground: !bg, clip: { x: 0, y: 0, width: w, height: h } });
    await page.close();
    console.log('png', out);
  }
  await browser.close();
})();
