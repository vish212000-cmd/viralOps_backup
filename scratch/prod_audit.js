const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://www.vishnumadapakula.in';

const routesToAudit = [
  { name: 'Dashboard', path: '/dashboard' },
  { name: 'Project Details', path: '/projects/1' },
  { name: 'Preferences', path: '/preferences' },
  { name: 'Analytics', path: '/analytics' },
  { name: 'Billing', path: '/billing' },
  { name: 'Admin Center', path: '/admin' }
];

async function run() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 }
  });
  
  // Set localStorage via a blank page on the domain
  const initPage = await context.newPage();
  
  // Intercept all api requests to mock auth and data
  await context.route('**/api/**', async route => {
    const requestUrl = route.request().url();
    if (requestUrl.includes('/api/auth/me')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          email: 'test@example.com',
          username: 'testuser',
          is_email_verified: true,
          is_mfa_enabled: false
        })
      });
    } else if (requestUrl.includes('/api/projects')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [{ id: 1, name: 'Mock Project', status: 'COMPLETED', created_at: new Date().toISOString() }],
          count: 1
        })
      });
    } else if (requestUrl.includes('/api/projects/1/')) {
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              id: 1, 
              name: 'Mock Project', 
              status: 'COMPLETED', 
              created_at: new Date().toISOString(),
              generated_assets: []
            })
          });
    } else {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({})
      });
    }
  });

  // Navigate to login just to set local storage on the origin
  await initPage.goto(BASE_URL + '/login', { waitUntil: 'domcontentloaded' });
  await initPage.evaluate(() => {
    localStorage.setItem('access_token', 'fake_token_for_prod_audit');
  });
  await initPage.close();

  const results = [];

  for (const route of routesToAudit) {
    const page = await context.newPage();
    console.log(`Auditing Production ${route.name} (${route.path})...`);
    await page.goto(BASE_URL + route.path, { waitUntil: 'networkidle' });

    // Ensure the page has loaded completely
    await page.waitForTimeout(2000); 

    const metrics = await page.evaluate(() => {
      // Find Sidebar
      let sidebarWidth = 0;
      let sidebar = document.querySelector('aside') || document.querySelector('.sidebar') || document.querySelector('[data-testid="sidebar"]');
      if (sidebar) {
        sidebarWidth = sidebar.getBoundingClientRect().width;
      }

      // Find Main content container
      let contentOffsetLeft = 0;
      let contentWidth = 0;
      let contentMarginLeft = '0px';
      let contentPaddingLeft = '0px';
      
      let mainContent = document.querySelector('main') || document.querySelector('.content-shell') || document.querySelector('.flex-1');
      
      if (mainContent) {
        const rect = mainContent.getBoundingClientRect();
        contentOffsetLeft = rect.left;
        contentWidth = rect.width;
        const computed = window.getComputedStyle(mainContent);
        contentMarginLeft = computed.marginLeft;
        contentPaddingLeft = computed.paddingLeft;
      }

      // Check heading overlap
      let headingOverlapsSidebar = false;
      let headingRect = null;
      let heading = document.querySelector('h1') || document.querySelector('h2');
      if (heading && sidebar) {
        const hRect = heading.getBoundingClientRect();
        const sRect = sidebar.getBoundingClientRect();
        headingRect = { left: hRect.left, top: hRect.top, width: hRect.width, height: hRect.height };
        // Overlap logic: if heading left is less than sidebar right AND heading top is within sidebar height
        if (hRect.left < sRect.right && hRect.right > sRect.left && hRect.top < sRect.bottom) {
            headingOverlapsSidebar = true;
        }
      }

      // Check overflow
      const bodyOverflowX = window.getComputedStyle(document.body).overflowX;
      const htmlOverflowX = window.getComputedStyle(document.documentElement).overflowX;

      return {
        sidebarWidth,
        contentOffsetLeft,
        contentWidth,
        contentMarginLeft,
        contentPaddingLeft,
        headingOverlapsSidebar,
        headingRect,
        bodyOverflowX,
        htmlOverflowX,
      };
    });

    // Save screenshot
    const screenshotPath = path.join(__dirname, `../artifacts/PROD_${route.name.replace(/\s+/g, '_')}_audit.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });

    results.push({
      ...route,
      ...metrics,
      screenshot: screenshotPath
    });

    await page.close();
  }

  await browser.close();
  fs.writeFileSync(path.join(__dirname, 'prod_audit_results.json'), JSON.stringify(results, null, 2));
  console.log('Prod Audit complete.');
}

run().catch(console.error);
