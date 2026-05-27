const puppeteer = require('/home/blxck/.local/lib/node_modules/@mermaid-js/mermaid-cli/node_modules/puppeteer');
const path = require('path');

const HTML = 'file://' + path.resolve(__dirname, 'script.html');
const OUT = path.resolve(__dirname, 'Sonar-сценарий.pdf');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/chromium',
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
  });
  const page = await browser.newPage();
  await page.goto(HTML, { waitUntil: 'networkidle0' });

  const headerTemplate = `
    <div style="font-family:'JetBrains Mono',monospace;font-size:7pt;color:#64748B;width:100%;padding:0 12mm;display:flex;justify-content:space-between;letter-spacing:0.04em;">
      <span>Sonar · сценарий</span>
      <span><span class="pageNumber"></span> / <span class="totalPages"></span></span>
    </div>`;

  await page.pdf({
    path: OUT,
    format: 'A5',
    margin: { top: '14mm', bottom: '10mm', left: '12mm', right: '12mm' },
    displayHeaderFooter: true,
    headerTemplate,
    footerTemplate: '<div></div>',
    printBackground: true,
  });

  await browser.close();
  console.log('saved', OUT);
})().catch(e => { console.error('ERR:', e.message); process.exit(1); });
