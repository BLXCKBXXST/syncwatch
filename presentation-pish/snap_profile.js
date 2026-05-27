const puppeteer = require('/home/blxck/.local/lib/node_modules/@mermaid-js/mermaid-cli/node_modules/puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/chromium',
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1440, height: 900 },
  });
  const page = await browser.newPage();

  // Go to profile — will redirect to login
  await page.goto('https://blxckhub.server34.netcraze.club/profile', {
    waitUntil: 'networkidle2',
    timeout: 30000,
  });

  await page.waitForSelector('input', { timeout: 10000 });

  // Probe inputs to understand selectors
  const inputs = await page.$$eval('input', els => els.map(el => ({
    type: el.type, name: el.name, placeholder: el.placeholder,
  })));
  console.error('inputs:', JSON.stringify(inputs));

  // Fill credentials
  const userInput = await page.$('input[type="text"], input[type="email"]');
  const passInput = await page.$('input[type="password"]');
  if (!userInput || !passInput) {
    throw new Error('login inputs not found');
  }
  await userInput.type(process.env.SONAR_USER);
  await passInput.type(process.env.SONAR_PASS);

  // Submit
  const submit = await page.$('button[type="submit"]');
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 }).catch(() => null),
    submit.click(),
  ]);
  // Extra settle time for SPA routing
  await new Promise(r => setTimeout(r, 4000));

  // Navigate to profile explicitly
  await page.goto('https://blxckhub.server34.netcraze.club/profile', {
    waitUntil: 'networkidle2',
    timeout: 30000,
  });
  await new Promise(r => setTimeout(r, 3000));

  await page.screenshot({ path: 'img/ui-profile.png' });
  console.error('ok: ui-profile.png');
  await browser.close();
})().catch(e => {
  console.error('ERR:', e.message);
  process.exit(1);
});
