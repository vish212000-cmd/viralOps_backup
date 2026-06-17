import json
import asyncio
from playwright.async_api import async_playwright

FRONTEND_URL = "https://viral-ops-backup-aexx.vercel.app"

report = {
    "frontend_errors": [],
    "network_failures": []
}

async def run_audit():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Listen for console errors
        page.on("pageerror", lambda err: report["frontend_errors"].append(str(err)))
        page.on("console", lambda msg: report["frontend_errors"].append(msg.text) if msg.type == "error" else None)
        
        # Listen for network errors (specifically chunk loading)
        page.on("response", lambda response: report["network_failures"].append({
            "url": response.url,
            "status": response.status
        }) if response.status >= 400 else None)
        
        print("Navigating to frontend...")
        try:
            await page.goto(FRONTEND_URL, wait_until="networkidle")
            
            # Try to trigger dynamic imports by navigating
            # We assume there's a login link or button
            print("Checking for login link...")
            login_links = await page.get_by_text("Log In").all()
            if login_links:
                await login_links[0].click()
                await page.wait_for_timeout(2000)
                
            signup_links = await page.get_by_text("Sign Up").all()
            if signup_links:
                await signup_links[0].click()
                await page.wait_for_timeout(2000)
                
        except Exception as e:
            report["frontend_errors"].append(str(e))
            
        await browser.close()
        
        with open("frontend_audit.json", "w") as f:
            json.dump(report, f, indent=2)
            
        print("Frontend audit complete. Errors found:", len(report["frontend_errors"]))
        for err in report["frontend_errors"]:
            print(" -", err)

if __name__ == "__main__":
    asyncio.run(run_audit())
