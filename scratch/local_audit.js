const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:5173';

const routesToAudit = [
  { name: 'Dashboard', path: '/dashboard' },
  { name: 'Project Details', path: '/projects/1' },
  { name: 'Preferences', path: '/preferences' },
  { name: 'Analytics', path: '/analytics' },
  { name: 'Billing', path: '/billing' },
  { name: 'Admin Center', path: '/admin' }
];

const viewports = [
  { name: 'Desktop', width: 1440, height: 900 },
  { name: 'Mobile', width: 390, height: 844 }
];

async function run() {
  const browser = await chromium.launch({ headless: true });
  
  const results = [];

  for (const vp of viewports) {
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
    
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
            id: 1, email: 'test@example.com', username: 'testuser', is_email_verified: true, is_mfa_enabled: false
          })
        });
      } else if (requestUrl.includes('/api/projects')) {
        return route.fulfill({
          status: 200, contentType: 'application/json',
          body: JSON.stringify({ results: [{ id: 1, name: 'Mock Project', status: 'COMPLETED', created_at: new Date().toISOString() }], count: 1 })
        });
      } else if (requestUrl.includes('/api/projects/1/')) {
          return route.fulfill({
              status: 200, contentType: 'application/json',
              body: JSON.stringify({ id: 1, name: 'Mock Project', status: 'COMPLETED', created_at: new Date().toISOString(), generated_assets: [] })
            });
      } else {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
      }
    });

    await initPage.goto(BASE_URL + '/login', { waitUntil: 'domcontentloaded' });
    await initPage.evaluate(() => { localStorage.setItem('access_token', 'fake_token_for_prod_audit'); });
    await initPage.close();

    for (const route of routesToAudit) {
      const page = await context.newPage();
      console.log(`Auditing Production ${route.name} on ${vp.name}...`);
      await page.goto(BASE_URL + route.path, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000); 

      const metrics = await page.evaluate(() => {
        let sidebar = document.querySelector('aside') || document.querySelector('.sidebar') || document.querySelector('[data-testid="sidebar"]');
        let sidebarRect = sidebar ? sidebar.getBoundingClientRect() : { width: 0, left: 0, right: 0 };

        let mainContent = document.querySelector('main') || document.querySelector('.content-shell') || document.querySelector('.flex-1') || document.querySelector('div[class*="ml-"]');
        let contentRect = mainContent ? mainContent.getBoundingClientRect() : { width: 0, left: 0, right: 0 };
        
        let contentMarginLeft = '0px';
        let contentPaddingLeft = '0px';
        if (mainContent) {
          const computed = window.getComputedStyle(mainContent);
          contentMarginLeft = computed.marginLeft;
          contentPaddingLeft = computed.paddingLeft;
        }

        let heading = document.querySelector('h1') || document.querySelector('h2');
        let headingRect = heading ? heading.getBoundingClientRect() : { width: 0, left: 0, right: 0 };

        let headingOverlapsSidebar = false;
        let contentOverlapsSidebar = false;

        if (sidebar && sidebarRect.width > 0) {
            if (heading && headingRect.left < sidebarRect.right && headingRect.right > sidebarRect.left) {
                headingOverlapsSidebar = true;
            }
            if (mainContent && contentRect.left < sidebarRect.right && contentRect.right > sidebarRect.left) {
                contentOverlapsSidebar = true;
            }
        }

        const bodyOverflowX = window.getComputedStyle(document.body).overflowX;
        const htmlOverflowX = window.getComputedStyle(document.documentElement).overflowX;
        const pageOverflows = document.documentElement.scrollWidth > window.innerWidth || document.body.scrollWidth > window.innerWidth;
        const contentBeginsAtZero = contentRect.left === 0;

        return {
          sidebar: { width: sidebarRect.width, left: sidebarRect.left, right: sidebarRect.right },
          content: { width: contentRect.width, left: contentRect.left, right: contentRect.right },
          heading: { width: headingRect.width, left: headingRect.left, right: headingRect.right },
          styles: {
            marginLeft: contentMarginLeft,
            paddingLeft: contentPaddingLeft,
            width: mainContent ? window.getComputedStyle(mainContent).width : '0px',
            overflowX: `${htmlOverflowX} (html), ${bodyOverflowX} (body)`
          },
          validation: {
            contentOverlapsSidebar,
            headingOverlapsSidebar,
            pageOverflows,
            contentBeginsAtZero
          }
        };
      });

      const filename = `PROD_${route.name.replace(/\s+/g, '_')}_${vp.name}.png`;
      const screenshotPath = path.join(__dirname, `../artifacts/${filename}`);
      await page.screenshot({ path: screenshotPath, fullPage: true });

      results.push({
        route: route.name,
        viewport: vp.name,
        url: BASE_URL + route.path,
        metrics,
        screenshotFilename: filename,
        screenshotPath
      });

      await page.close();
    }
    await context.close();
  }

  await browser.close();
  fs.writeFileSync(path.join(__dirname, 'prod_audit_v2_results.json'), JSON.stringify(results, null, 2));
  console.log('Prod Audit V2 complete.');
}

run().catch(console.error);
