import asyncio
from playwright.async_api import async_playwright
import os

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to app...")
        await page.goto("http://localhost:8501")
        await page.wait_for_selector('input[type="file"]')
        
        print("Uploading files...")
        files = [
            r"D:\Google Antigravity\work-place\Data test\TNS 3_20260220183710_average.txt",
            r"D:\Google Antigravity\work-place\Data test\TNS 3_20260220183720_average.txt",
            r"D:\Google Antigravity\work-place\Data test\TNS 3_20260220183737_average.txt"
        ]
        await page.locator('input[type="file"]').set_input_files(files)
        
        # Wait for "KPI" or "Raw -> Averaged" to indicate load completion
        print("Waiting for data to load...")
        await page.wait_for_selector('text=Raw \u2192 Averaged', timeout=10000)
        
        print("Clicking ROI Tab...")
        await page.click('button[data-baseweb="tab"]:has-text("ROI & Fitting")')
        
        print("Clicking Raw scans view mode...")
        await page.click('text=Raw scans (select/exclude)')
        
        print("Waiting for checkboxes...")
        await page.wait_for_selector('input[type="checkbox"]', state='visible')
        
        # Uncheck the first data checkbox (the 3rd checkbox on the page, after "Remove outliers" and "Use averaged data" maybe)
        # Let's just find the checkbox associated with the file
        print("Excluding first scan...")
        await page.click('text=TNS 3_20260220183710_average.txt')
        
        print("Clicking Re-average...")
        await page.click('text=Apply & Re-average')
        
        print("Waiting 3s for rerun...")
        await asyncio.sleep(3)
        
        print("Checking if plot changed or anything... Done.")
        await browser.close()

asyncio.run(run())
