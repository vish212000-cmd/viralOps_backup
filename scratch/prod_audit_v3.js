const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://www.vishnumadapakula.in';

const routesToAudit = [
  { name: 'Dashboard', path: '/dashboard' },
  { name: 'Preferences', path: '/preferences' },
  { name: 'Analytics', path: '/analytics' },
  { name: 'Billing', path: '/billing' },
  { name: 'Project Details', path: '/projects/1' },
  { name: 'Admin Dashboard', path: '/admin' }
];

async function run() {
  const browser = await chromium.launch({ headless: true });
  const results = {};

  for (const route of routesToAudit) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    
    let consoleErrors = [];
    let networkErrors = [];
    let finalUrl = '';
    let httpStatus = 0;

    const page = await context.newPage();

    page.on('console', msg => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    
    page.on('response', response => {
      if (!response.ok() && response.request().resourceType() === 'fetch') {
         networkErrors.push(`${response.status()} ${response.url()}`);
      }
    });

    // We will set localStorage tokens first
    await page.goto(BASE_URL + '/login', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => {
        localStorage.setItem('access_token', 'fake_token_for_prod_audit');
        localStorage.setItem('user', JSON.stringify({id: 1, is_superuser: true, role: 'admin'}));
    });

    // Intercept to mock APIs
    await context.route('**/api/**', async routeReq => {
      const requestUrl = routeReq.request().url();
      if (requestUrl.includes('/api/auth/me')) {
        return routeReq.fulfill({
          status: 200, contentType: 'application/json',
          body: JSON.stringify({ id: 1, email: 'test@example.com', is_superuser: true, role: 'admin' })
        });
      }
      if (requestUrl.includes('/api/projects')) {
        return routeReq.fulfill({
          status: 200, contentType: 'application/json',
          body: JSON.stringify({ id: 1, name: 'Mock Project', status: 'COMPLETED' })
        });
      }
      return routeReq.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });

    console.log(`Auditing ${route.name}...`);
    const response = await page.goto(BASE_URL + route.path, { waitUntil: 'networkidle' });
    
    httpStatus = response ? response.status() : 0;
    await page.waitForTimeout(2000); // let React render

    finalUrl = page.url();

    const domStats = await page.evaluate(() => {
      return {
        reactMounted: !!document.getElementById('root')?.hasChildNodes(),
        appLayoutExists: !!document.querySelector('.app-layout') || !!document.querySelector('[data-testid="app-layout"]'),
        sidebarExists: !!document.querySelector('aside') || !!document.querySelector('.sidebar') || !!document.querySelector('[data-testid="sidebar"]'),
        contentShellExists: !!document.querySelector('.content-shell') || !!document.querySelector('main') || !!document.querySelector('.flex-1')
      };
    });

    const screenshotName = `PROD_V3_${route.name.replace(/\s+/g, '_')}.png`;
    const screenshotPath = path.join(__dirname, `../artifacts/${screenshotName}`);
    await page.screenshot({ path: screenshotPath, fullPage: true });

    let reasonForZeroWidth = null;
    if (finalUrl !== BASE_URL + route.path) {
        reasonForZeroWidth = 'route guard redirect';
    } else if (!domStats.reactMounted) {
        reasonForZeroWidth = 'React crash';
    } else if (httpStatus >= 400) {
        reasonForZeroWidth = httpStatus.toString();
    } else if (networkErrors.length > 0) {
        reasonForZeroWidth = 'API failure';
    } else if (!domStats.contentShellExists) {
        reasonForZeroWidth = 'selector failure';
    }

    results[route.name] = {
      httpStatus,
      finalUrl,
      ...domStats,
      consoleErrors,
      networkErrors,
      screenshotName,
      screenshotPath,
      reasonForZeroWidth
    };

    await context.close();
  }

  await browser.close();
  fs.writeFileSync(path.join(__dirname, 'prod_audit_v3_results.json'), JSON.stringify(results, null, 2));
  console.log('Prod Audit V3 complete.');
}

run().catch(console.error);
