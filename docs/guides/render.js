// Print one HTML file to a PDF (A4), for docs/guides/build_guides.py.
//
//   node docs/guides/render.js <page.html> <out.pdf>
//   node docs/guides/render.js <page.html> <out.pdf> --cover          one page with no margin
//
// The page's own stylesheet sets the paper, the margins and the foot of each page (guides.css, @page).
// Needs Playwright with Chromium.

const { chromium } = require('playwright');

(async () => {
  const [, , input, output, mode] = process.argv;
  if (!input || !output) { console.error('usage: node render.js <page.html> <out.pdf> [--cover]'); process.exit(2); }
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + input, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  if (mode === '--cover') await page.pdf({ path: output, format: 'A4', printBackground: true, margin: { top: '0', bottom: '0', left: '0', right: '0' }, pageRanges: '1' });
  else await page.pdf({ path: output, printBackground: true, preferCSSPageSize: true, outline: true, tagged: true });
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
