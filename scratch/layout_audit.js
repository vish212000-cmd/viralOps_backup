const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const token = fs.readFileSync(path.join(__dirname, '../backend/token.txt'), 'utf8')
  .split('\n')[0]
  .replace('ACCESS_TOKEN=', '')
  .trim();

const BASE_URL = 'http://localhost:5173';

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
  
  // Set localStorage via a blank page
  const initPage = await context.newPage();
  await initPage.goto(BASE_URL + '/login'); // go to a valid origin
  await initPage.evaluate((token) => {
    localStorage.setItem('access_token', token);
  }, token);
  await initPage.close();

  const results = [];

  for (const route of routesToAudit) {
    const page = await context.newPage();
    console.log(`Auditing ${route.name} (${route.path})...`);
    await page.goto(BASE_URL + route.path, { waitUntil: 'networkidle' });

    // Ensure the page has loaded completely
    await page.waitForTimeout(2000); // give it time to render

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
      
      let mainContent = document.querySelector('main') || document.querySelector('.content-shell') || document.querySelector('.flex-1');
      
      if (mainContent) {
        const rect = mainContent.getBoundingClientRect();
        contentOffsetLeft = rect.left;
        contentWidth = rect.width;
      }

      // Find if AppLayout is used
      const hasAppShell = document.querySelector('.app-shell') !== null;
      
      // Find any elements with ml-* or pl-*
      // We look at the body elements and check computed styles or class names
      const allElements = document.querySelectorAll('*');
      let compensationClasses = false;
      let fixedOrAbsolute = false;
      
      for (const el of allElements) {
        const className = el.className;
        if (typeof className === 'string' && className.match(/(?:^|\s)(ml-|pl-)(64|72|80|256|280)(?:$|\s)/)) {
          compensationClasses = true;
        }
        
        // Exclude the sidebar itself and obvious generic fixed items (like toasts)
        // Let's check main layout wrappers
        if (el.tagName.toLowerCase() === 'main' || el.tagName.toLowerCase() === 'div') {
            const style = window.getComputedStyle(el);
            // If the element takes up a significant portion of the screen and is fixed
            if ((style.position === 'fixed' || style.position === 'absolute') && el.getBoundingClientRect().width > window.innerWidth * 0.5) {
                // Ignore the mobile overlay
                if (!className.includes('inset-0')) {
                    fixedOrAbsolute = true;
                }
            }
        }
      }

      // Check overflow
      const bodyOverflowX = window.getComputedStyle(document.body).overflowX;
      const htmlOverflowX = window.getComputedStyle(document.documentElement).overflowX;
      const mainOverflowX = mainContent ? window.getComputedStyle(mainContent).overflowX : 'N/A';

      // Dom hierarchy depth
      let maxDepth = 0;
      const getDepth = (node, depth) => {
        if (depth > maxDepth) maxDepth = depth;
        for (let i = 0; i < node.childNodes.length; i++) {
          getDepth(node.childNodes[i], depth + 1);
        }
      };
      getDepth(document.body, 1);

      return {
        sidebarWidth,
        contentOffsetLeft,
        contentWidth,
        hasAppShell,
        compensationClasses,
        fixedOrAbsolute,
        bodyOverflowX,
        htmlOverflowX,
        mainOverflowX,
        domDepth: maxDepth
      };
    });

    // Save screenshot
    const screenshotPath = path.join(__dirname, `../artifacts/${route.name.replace(/\s+/g, '_')}_layout_audit.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });

    results.push({
      ...route,
      ...metrics,
      screenshot: screenshotPath
    });

    await page.close();
  }

  await browser.close();
  fs.writeFileSync(path.join(__dirname, 'layout_audit_results.json'), JSON.stringify(results, null, 2));
  console.log('Audit complete.');
}

run().catch(console.error);
