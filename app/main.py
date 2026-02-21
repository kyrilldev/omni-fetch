import asyncio
import sys

# Windows-specifieke fix voor Playwright NotImplementedError
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, HTTPException
from app.database import Database
from app.schemas import ScrapeRequest, ScrapeResponse, DetectSelectorRequest, DetectSelectorResponse, Blueprint
from app.engine import Engine

# Forceer ProactorEventLoop op Windows voor Playwright
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


# 1. Definieer de app op het hoogste niveau (top-level)
app = FastAPI(
    title="OmniFetch",
    description="High-performance local scraping API",
    version="0.1.0"
)

# 2. Maak één globale instance van de Engine (Singleton-patroon)
# Dit zorgt ervoor dat je browser open blijft en snel is.

omni_engine = Engine()
omni_engine.setup()

db = Database()

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
        print(f"content: {content}")
        
        return DetectSelectorResponse(url=url, selectors=content, success=True)
    except Exception as e:
        return DetectSelectorResponse(
            url=str(payload.url),
            selectors={},
            success=False,
            error=str(e)
        )
        
@app.post("/api/v1/generate")
async def generate_endpoint(payload: DetectSelectorRequest):
    import uuid
    api_id = f"api-{str(uuid.uuid4())[:8]}"
    local_link = f"http://localhost:8000/api/v1/run/{api_id}"
    try:
        # 1. Genereer een unieke ID voor dit endpoint
        # Bijv: 'weather-api-f47ac10b'
        
        response = await detect_selectors_endpoint(payload=payload)
        
        success = db.save_blueprint(
            api_id=api_id, 
            selectors=response.selectors, 
            url=str(payload.url) 
        )
        
        return Blueprint(api_id=api_id, endpoint=local_link, success=success)
        
    except Exception as e:
        return Blueprint(api_id=api_id, endpoint=local_link, success=False, error=str(e))

@app.get("/api/v1/run/{run_id}", response_model=ScrapeResponse)
async def dynamic_api_endpoint(run_id: str):
    # 1. Haal de blauwdruk op uit de database
    blueprint = db.get_blueprint(run_id)
    
    # 2. Error handling als de ID niet bestaat
    if not blueprint:
        return ScrapeResponse(
            url="unknown",
            data={}, # Lege dict voor de resultaten
            success=False,
            error=f"Blueprint met ID {run_id} niet gevonden in de database."
        )

    try: 
        # 3. Pak de bron-URL en de opgeslagen selectors
        target_url = blueprint['url']
        saved_selectors = blueprint['selectors']
        
        # 4. Voer de daadwerkelijke scraping uit met de Engine
        # results bevat nu de tekst die bij de selectors hoort
        results = await omni_engine.extract_data(target_url, saved_selectors)
        
        # 5. Geef het resultaat terug in het ScrapeResponse formaat
        return ScrapeResponse(
            url=target_url,
            data=results,  # De gescrapete tekst (bijv. {"titel": "Kasteel Karlstein"})
            success=True
        )
        
    except Exception as e:
        # 6. Fallback voor als de website offline is of de scraping faalt
        return ScrapeResponse(
            url=blueprint.get('url', "unknown"),
            data={},
            success=False,
            error=f"Scraping fout: {str(e)}"
        )

# 3. Optioneel: Sluit de browser netjes af als de server stopt
@app.on_event("shutdown")
async def shutdown_event():
    await omni_engine.shutdown()
    
