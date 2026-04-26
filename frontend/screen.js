const { chromium } = require('playwright');

const BASE_URL = 'http://127.0.0.1:5173';
const PAGES = [
  { path: '/', name: 'dashboard' },
  { path: '/login', name: 'login' },
  { path: '/agents', name: 'agents' },
  { path: '/tasks', name: 'tasks' },
  { path: '/approvals', name: 'approvals' },
  { path: '/billing', name: 'billing' },
  { path: '/audit-log', name: 'audit-log' },
  { path: '/hierarchy', name: 'hierarchy' },
  { path: '/integrations', name: 'integrations' },
  { path: '/settings', name: 'settings' },
];

async function captureScreenshots() {
  console.log('Starting browser...');
  const browser = await chromium.launch({ headless: true });
  console.log('Browser launched');
  
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  
  for (const pageInfo of PAGES) {
    const page = await context.newPage();
    try {
      console.log('Navigating to ' + pageInfo.path + '...');
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
  console.log('Done!');
}

captureScreenshots().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
