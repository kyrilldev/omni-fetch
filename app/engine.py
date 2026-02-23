from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
from typing import Dict, Any
import openai
import pprint

class Engine:
    def __init__(self, cloud):
        self.browser = None
        self.playwright = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        self.llm_model = None
        self.cloud = cloud
        self.client = openai.OpenAI(api_key="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", base_url="https://openrouter.ai/api/v1")
        
    async def setup(self):
        self._ensure_browser()
        self.llm_model = await self._ensure_llm()

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
                if not node:
                    print(f"⚠️ Waarschuwing: Selector voor '{field}' ({selector}) vond niets op {url}")
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
        if self.cloud:
            return
        
        models = await self._check_models()
        
        try:
            model_string = models.models[0]['model']
            
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
        
        print("here2")
        
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
    
    async def extract_selectors(self, url: str, prompt="Geef me de titel en de eerste alinea.") -> Dict[str, str]:
        import ollama
        import json
        await self._ensure_browser()
        self.llm_model = await self._ensure_llm()
        
        context = await self.browser.new_context(user_agent=self.user_agent)
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            html_content = await page.content()
            
            pprint.pp(html_content)
            
            with open("html_content.txt", "w", encoding="utf-8") as f:
                f.write(html_content)
            
            tree = HTMLParser(html_content)
            
            # 1. Verwijder de rommel die we echt niet nodig hebben
            for tag in tree.css('script, style, noscript, svg, nav, footer, header, iframe'):
                tag.decompose()
            
            # 2. Verzamel ALLE tekst-bevattende elementen
                simplified_blocks = []
                
                # We kijken naar alle elementen in de body
                for el in tree.body.css('*'):
                    # Pak de tekstuele inhoud
                    content = el.text(strip=True)
                    
                    # Selectolax check: heeft dit element directe tekst kinderen?
                    # We kijken of het element zelf tekst bevat, maar niet te groot is (ruis-filter)
                    if content and len(content) < 500: 
                        # Check of het element 'eindpunt' is (geen andere HTML tags erin)
                        # In Selectolax gebruiken we el.child om te zien of er diepere nesting is
                        if el.child is None or el.child.tag == "-text":
                            tag_name = el.tag
                            tag_class = f" class='{el.attributes.get('class')}'" if el.attributes.get('class') else ""
                            tag_id = f" id='{el.attributes.get('id')}'" if el.attributes.get('id') else ""
                            
                            # Voeg het element toe als een compacte string
                            simplified_blocks.append(f"<{tag_name}{tag_id}{tag_class}>{content}</{tag_name}>")

            # Maak er één grote string van voor de AI
            # We gebruiken een set() om duplicaten te voorkomen en joinen met newlines
            html_skeleton = "\n".join(list(dict.fromkeys(simplified_blocks)))

            system_instruction = (
                "You are a Web Scraping Expert. Extract CSS selectors for the user's request.\n"
                "I provide a list of HTML elements that contain text. Your job is to pick the best CSS selector.\n"
                "Rules:\n"
                "1. Use the tags, IDs, and classes provided to build unique selectors.\n"
                "2. Return ONLY a JSON object with the requested fields.\n"
                "3. Never return the text content, only the selectors."
            )
            
            if self.cloud:
                try: 
                    pprint.pp(html_skeleton)
                    cloud_response = self.client.chat.completions.create(
                        # model="openai/gpt-oss-120b:free",
                        model="minimax/minimax-m2.5",
                        messages=[
                            {'role': 'system', 'content': system_instruction},
                            {'role': 'user', 'content': f"HTML Elements:\n{html_skeleton}"},
                            {'role': 'user', 'content': f"Opdracht: {prompt}"},
                        ],
                        )
                    
                    pprint.pp(cloud_response.choices[0].message.content)
                    
                    return json.loads(cloud_response.choices[0].message.content)
                except Exception as e:
                    return {"error": str(e)}
            else:
                response = ollama.chat(
                    model=self.llm_model,
                    messages=[
                        {'role': 'system', 'content': system_instruction},
                        {'role': 'user', 'content': f"HTML Elements:\n{html_skeleton}"},
                        {'role': 'user', 'content': f"Opdracht: {prompt}"},
                    ],
                    format='json'
                )
                return json.loads(response['message']['content'])

        finally:
            await page.close()
            await context.close()