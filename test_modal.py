import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(record_video_dir="artifacts/videos", viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        print("Navigating to Dashboard...")
        await page.goto("http://localhost:5173/dashboard")
        
        # Wait for page to load
        await page.wait_for_timeout(2000)
        
        # Open "Create New Project" modal
        print("Opening modal...")
        await page.click("text=Create New Project")
        await page.wait_for_timeout(1000)
        
        # Select "PDF" or "VIDEO"
        print("Clicking Video type...")
        await page.click("text=Video")
        await page.wait_for_timeout(500)
        
        # Upload a dummy file (create one if necessary)
        import os
        dummy_file = "test_video.mp4"
        with open(dummy_file, "wb") as f:
            f.write(b"\x00" * 1024 * 1024)  # 1MB dummy video
            
        print("Uploading file...")
        await page.set_input_files("input[type='file']", dummy_file)
        await page.wait_for_timeout(1000)
        
        # Fill in long description
        print("Filling description...")
        long_desc = "This is a very long description to ensure the form is extremely tall. " * 50
        # If there's a text area
        textareas = await page.query_selector_all("textarea")
        if textareas:
            await textareas[0].fill(long_desc)
        
        await page.wait_for_timeout(500)
        
        # Take screenshot of top
        print("Screenshot top...")
        await page.screenshot(path="artifacts/top_of_modal.png")
        
        # Get DOM Metrics
        print("Extracting DOM metrics...")
        metrics = await page.evaluate('''() => {
            const container = document.querySelector('.overflow-y-auto');
            if (!container) return { error: "Container not found" };
            return {
                clientHeight: container.clientHeight,
                scrollHeight: container.scrollHeight,
                overflowY: window.getComputedStyle(container).overflowY
            };
        }''')
        
        print("Metrics:", json.dumps(metrics, indent=2))
        
        # Scroll down
        print("Scrolling down...")
        await page.evaluate('''() => {
            const container = document.querySelector('.overflow-y-auto');
            if (container) container.scrollTo({top: container.scrollHeight, behavior: 'smooth'});
        }''')
        
        await page.wait_for_timeout(1000)
        
        # Take screenshot of bottom
        print("Screenshot bottom...")
        await page.screenshot(path="artifacts/bottom_of_modal.png")
        
        # Check if Submit button is visible
        submit_btn = await page.query_selector("button[type='submit']")
        is_visible = await submit_btn.is_visible() if submit_btn else False
        print("Submit button visible:", is_visible)
        
        await context.close()
        await browser.close()
        os.remove(dummy_file)

if __name__ == "__main__":
    asyncio.run(main())
