// Print one HTML file to a PDF (A4), for docs/guides/build_guides.py.
//
//   node docs/guides/render.js <page.html> <out.pdf> "<footer text>"
//   node docs/guides/render.js <page.html> <out.pdf> --cover          one page with no margin and no footer
//
// The page's own stylesheet sets the margins (guides.css, @page); the footer carries the guide's name and the page number.
// Needs Playwright with Chromium.

const { chromium } = require('playwright');

(async () => {
  const [, , input, output, footer] = process.argv;
  if (!input || !output) { console.error('usage: node render.js <page.html> <out.pdf> "<footer text>"'); process.exit(2); }
  const esc = (s) => String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + input, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  if (footer === '--cover') {
    await page.pdf({ path: output, format: 'A4', printBackground: true, margin: { top: '0', bottom: '0', left: '0', right: '0' }, pageRanges: '1' });
    await browser.close();
    return;
  }
  await page.pdf({
    path: output, format: 'A4', printBackground: true, preferCSSPageSize: true, displayHeaderFooter: true, outline: true, tagged: true,
    headerTemplate: '<span></span>',
    footerTemplate: '<div style="width:100%;margin:0 18mm;font-family:Inter,Arial,sans-serif;font-size:7.5pt;color:#7a8696;display:flex;justify-content:space-between;">' +
      '<span>' + esc(footer) + '</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
    margin: { top: '20mm', bottom: '20mm', left: '18mm', right: '18mm' },
  });
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
