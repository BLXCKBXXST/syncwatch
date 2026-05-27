const puppeteer = require('/home/blxck/.local/lib/node_modules/@mermaid-js/mermaid-cli/node_modules/puppeteer');

const BASE = 'https://blxckhub.server34.netcraze.club';
const ROOM = '/room/d4245ece-9791-41dc-9b07-52028e6fefc0';

const wait = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/chromium',
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1600, height: 820 },
  });
  const page = await browser.newPage();

  // 1. Login
  console.error('→ login');
  await page.goto(BASE + '/login', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForSelector('input[name="username"]', { timeout: 10000 });
  await page.type('input[name="username"]', process.env.SONAR_USER);
  await page.type('input[name="password"]', process.env.SONAR_PASS);
  await page.click('button[type="submit"]');
  await wait(5000);
  console.error('  logged in, current URL:', page.url());

  // 2. Snap home
  console.error('→ home');
  await page.goto(BASE + '/', { waitUntil: 'networkidle2', timeout: 30000 });
  await wait(3000);
  await page.screenshot({ path: 'img/ui-home.png' });
  console.error('  saved ui-home.png');

  // 3. Snap room
  console.error('→ room');
  await page.goto(BASE + ROOM, { waitUntil: 'networkidle2', timeout: 30000 });
  await wait(4000);
  await page.screenshot({ path: 'img/ui-room.png' });
  console.error('  saved ui-room.png');

  // 4. Snap profile
  console.error('→ profile');
  await page.goto(BASE + '/profile', { waitUntil: 'networkidle2', timeout: 30000 });
  await wait(3000);
  await page.screenshot({ path: 'img/ui-profile.png' });
  console.error('  saved ui-profile.png');

  await browser.close();
  console.error('done');
})().catch(e => {
  console.error('ERR:', e.message);
  process.exit(1);
});
