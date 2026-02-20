import asyncio
import sys
from fastapi import FastAPI, HTTPException

# Forceer ProactorEventLoop op Windows voor Playwright
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.schemas import ScrapeRequest, ScrapeResponse, DetectSelectorRequest, DetectSelectorResponse
from app.engine import Engine

# 1. Definieer de app op het hoogste niveau (top-level)
app = FastAPI(
    title="OmniFetch",
    description="High-performance local scraping API",
    version="0.1.0"
)

# 2. Maak één globale instance van de Engine (Singleton-patroon)
# Dit zorgt ervoor dat je browser open blijft en snel is.
omni_engine = Engine()

@app.post("/extract", response_model=ScrapeResponse)
async def extract_endpoint(payload: ScrapeRequest):
    try:
        url_str = str(payload.url)
        # Gebruik de globale engine in plaats van elke keer een nieuwe te maken
        data = await omni_engine.extract_data(url_str, payload.selectors)
        return ScrapeResponse(url=url_str, data=data, success=True)
    
    except Exception as e:
        return ScrapeResponse(
            url=str(payload.url),
            data={},
            success=False,
            error=str(e)
        )

@app.post("/detect-selectors", response_model=DetectSelectorResponse)
async def detect_selectors_endpoint(payload: DetectSelectorRequest):
    """
    Hier komt je AI-logica. 
    Stappen: 
    1. Haal HTML op met omni_engine.
    2. Gebruik een 'distiller' om alleen tekst/markdown over te houden.
    3. Stuur naar Ollama.
    """
    try:
        url = str(payload.url)
        prompt = payload.user_prompt
        # TODO: Implementeer AI logica
        content = await omni_engine.extract_selectors(url, prompt)
        
        import json
        content = json.loads(content)
        
        print(f"content: {content}")
        return DetectSelectorResponse(url=url, selectors=content, success=True)
    except Exception as e:
        return DetectSelectorResponse(
            url=str(payload.url),
            selectors={},
            success=False,
            error=str(e)
        )

# 3. Optioneel: Sluit de browser netjes af als de server stopt
@app.on_event("shutdown")
async def shutdown_event():
    await omni_engine.shutdown()