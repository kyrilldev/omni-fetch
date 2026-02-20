from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
from typing import Dict, Any

async def extract_data(url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
    """
    Launches a browser, navigates to the URL, and extracts data using Selectolax.
    """
    async with async_playwright() as p:
        # Launch headless Chromium
        # In a production environment, consider managing a persistent browser context
        # to avoid the overhead of launching the browser for every request.
        browser = await p.chromium.launch(headless=True)
        
        # Create a context with a standard user agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        page = await context.new_page()

        try:
            # Optimization: Block unnecessary resources to speed up loading
            await page.route("**/*", lambda route: route.abort() 
                             if route.request.resource_type in ["image", "media", "font"] 
                             else route.continue_())

            # Navigate to the URL
            # wait_until='domcontentloaded' is usually sufficient for scraping and faster than 'networkidle'
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Get the raw HTML
            html_content = await page.content()
            
            # Parse with Selectolax (extremely fast)
            tree = HTMLParser(html_content)
            
            results = {}
            for field, selector in selectors.items():
                node = tree.css_first(selector)
                results[field] = node.text(strip=True) if node else None
                
            return results

        finally:
            await browser.close()