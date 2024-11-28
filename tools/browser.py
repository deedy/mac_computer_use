from playwright.async_api import async_playwright

class BrowserTool:
    """Modern browser automation with Playwright"""
    
    async def setup_browser(self):
        """Initialize browser with optimized settings"""
        self.playwright = await async_playwright().start()
        return await self.playwright.chromium.launch(
            args=[
                '--enable-gpu-rasterization',
                '--enable-zero-copy',
                '--disable-gpu-sandbox',
                '--enable-hardware-overlays',
                '--ignore-gpu-blocklist'
            ]
        )

    async def capture_page(self, url: str) -> ToolResult:
        """Capture page with hardware acceleration"""
        browser = await self.setup_browser()
        page = await browser.new_page()
        
        # Enable smooth scrolling
        await page.evaluate("""
            Object.defineProperty(document.documentElement, 'scrollBehavior', {
                value: 'smooth',
                writable: true
            });
        """)
        
        await page.goto(url)
        screenshot = await page.screenshot(full_page=True)
        await browser.close()
        
        return ToolResult(base64_image=base64.b64encode(screenshot).decode()) 