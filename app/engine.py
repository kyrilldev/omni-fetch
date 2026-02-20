from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
from typing import Dict, Any

class Engine:
    def __init__(self):
        self.browser = None
        self.playwright = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        self.llm_model = None

    async def _ensure_browser(self):
        """Helper to ensure browser is running without async __init__"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
        if not self.browser:
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-http2",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--proxy-server='direct://'",
                    "--proxy-bypass-list=*"
                ]
            )
            print("🚀 Browser Instance Started")

    async def extract_data(self, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        await self._ensure_browser()
        
        # Create a fresh context for every request (better than a fresh browser)
        context = await self.browser.new_context(user_agent=self.user_agent)
        
        
        page = await context.new_page()

        try:
            # Block heavy stuff
            await page.route("**/*", lambda route: route.abort() 
                            if route.request.resource_type in ["image", "media", "font"] 
                            else route.continue_())

            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            html_content = await page.content()
            
            tree = HTMLParser(html_content)
            
            print(tree)
            results = {}
            for field, selector in selectors.items():
                node = tree.css_first(selector)
                results[field] = node.text(strip=True) if node else None
                
            return results

        finally:
            # ONLY close the page/context, keep the browser alive!
            await page.close()
            await context.close()

    async def shutdown(self):
        """Call this when the FastAPI server stops"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    async def _ensure_llm(self):
        models = await self._check_models()
        
        try:
            
            model_string = models.models[0]['model']
            
            print(model_string)
            
            self._preload_model(model_string)
            
            return model_string
        
        except Exception as e:
            print(str(e)) 
        
    def _preload_model(self, model_name:str):
        import ollama
        ollama.generate(model=model_name, prompt="")
        print(f"Model {model_name} is geladen en klaar voor gebruik.")
    
    async def _check_models(self):
        import ollama
        
        model_list = ollama.list()
        
        if len(model_list.models) <= 0:
            for progress in ollama.pull('llama3.2'):
                status = progress.get('status')
                digest = progress.get('digest')
                total = progress.get('total')
                completed = progress.get('completed')

                if digest != current_digest:
                    print(f"\nNieuw segment: {digest}")
                    current_digest = digest

                if total and completed:
                    percentage = (completed / total) * 100
                    # Print de voortgang op dezelfde regel
                    print(f"\rStatus: {status} - {percentage:.2f}%", end="", flush=True)
                else:
                    print(f"\rStatus: {status}", end="")
            
        return model_list
    
    async def extract_selectors(self, url: str, prompt="Geef me de naam van het kasteel en de eerste alinea tekst.",) -> Dict[str, str]:
        import ollama
        await self._ensure_browser()
        model_name = await self._ensure_llm()
        
        # Create a fresh context for every request (better than a fresh browser)
        context = await self.browser.new_context(user_agent=self.user_agent)
        
        page = await context.new_page()

        try:
            # Block heavy stuff
            await page.route("**/*", lambda route: route.abort() 
                            if route.request.resource_type in ["image", "media", "font"] 
                            else route.continue_())

            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            html_content = await page.content()
            
            tree = HTMLParser(html_content)
            
            for tag in tree.css('script, style, noscript, svg, nav, footer, header'):
                tag.decompose()
            
            only_text_website = tree.body.text(separator='\n', strip=True)
            
            system_instruction = (
                "You are a data-extractor assistent. "
                "Use the following text from the website to answer the questions of the user. "
                "ALWAYS give the answer in pure JSON-format."
            )
                
            response = ollama.chat(
                model=model_name,
                messages=[
                    {'role': 'user', 'content': f"Website text: {only_text_website}"},
                    {'role': 'user', 'content': f"Opdracht: {prompt}"},
                ],
                format='json'
            )
                
            return response['message']['content']

        finally:
            # ONLY close the page/context, keep the browser alive!
            await page.close()
            await context.close()