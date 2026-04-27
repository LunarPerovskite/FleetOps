const { chromium } = require('playwright');

const BASE_URL = 'http://127.0.0.1:5173';
const PAGES = [
  { path: '/', name: 'dashboard-colored' },
  { path: '/analytics', name: 'analytics-colored' },
  { path: '/agents', name: 'agents-colored' },
  { path: '/tasks', name: 'tasks-colored' },
  { path: '/approvals', name: 'approvals-colored' },
];

async function captureScreenshots() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  
  for (const pageInfo of PAGES) {
    const page = await context.newPage();
    try {
      await page.goto(BASE_URL + pageInfo.path, { waitUntil: 'networkidle', timeout: 15000 });
      await page.waitForTimeout(2000);
      
      const screenshotPath = '/data/.openclaw/workspace/fleetops-temp/docs/screenshots/' + pageInfo.name + '.png';
      await page.screenshot({ path: screenshotPath, fullPage: true });
      console.log('OK ' + pageInfo.name + ': ' + screenshotPath);
    } catch (err) {
      console.log('FAIL ' + pageInfo.name + ': ' + err.message);
    }
    await page.close();
  }
  
  await browser.close();
}

captureScreenshots().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
