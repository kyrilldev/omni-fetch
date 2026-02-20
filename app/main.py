from fastapi import FastAPI, HTTPException
from app.schemas import ScrapeRequest, ScrapeResponse
from app.engine import extract_data

app = FastAPI(
    title="OmniFetch",
    description="High-performance local scraping API",
    version="0.1.0"
)

@app.post("/extract", response_model=ScrapeResponse)
async def extract_endpoint(payload: ScrapeRequest):
    """
    Extracts data from a target URL based on provided CSS selectors.
    """
    try:
        # Convert HttpUrl to string for the engine
        url_str = str(payload.url)
        
        data = await extract_data(url_str, payload.selectors)
        
        return ScrapeResponse(url=url_str, data=data)
    
    except Exception as e:
        return ScrapeResponse(
            url=str(payload.url),
            data={},
            success=False,
            error=str(e)
        )