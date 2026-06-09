import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    report = {
        "console_errors": [],
        "network_errors": [],
        "js_exceptions": []
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        page.on("console", lambda msg: report["console_errors"].append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: report["js_exceptions"].append(str(exc)))
        
        async def on_response(response):
            if response.status >= 400:
                report["network_errors"].append(f"{response.status} - {response.url}")

        page.on("response", on_response)

        routes = [
            {"name": "Homepage", "url": "https://viral-ops-backup-aexx.vercel.app/"},
            {"name": "Login", "url": "https://viral-ops-backup-aexx.vercel.app/login"},
            {"name": "Signup", "url": "https://viral-ops-backup-aexx.vercel.app/signup"},
            {"name": "Dashboard", "url": "https://viral-ops-backup-aexx.vercel.app/dashboard"}
        ]

        for route in routes:
            try:
                await page.goto(route["url"], wait_until="networkidle")
                await page.screenshot(path=f"C:/Users/TCCSPL/.gemini/antigravity/brain/afc95b85-e151-49f3-acd4-9fff6b88a2ad/{route['name']}.png")
                await asyncio.sleep(1) # wait for any lazy load
            except Exception as e:
                report["js_exceptions"].append(f"Failed to load {route['url']}: {str(e)}")

        await browser.close()

    with open('C:/Users/TCCSPL/.gemini/antigravity/brain/afc95b85-e151-49f3-acd4-9fff6b88a2ad/browser_results.json', 'w') as f:
        json.dump(report, f)

if __name__ == "__main__":
    asyncio.run(run())
