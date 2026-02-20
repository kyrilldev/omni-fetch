from typing import Dict, Any, Optional
from pydantic import BaseModel, HttpUrl

class ScrapeRequest(BaseModel):
    """
    Payload for the extraction endpoint.
    """
    url: HttpUrl
    selectors: Dict[str, str]  # Key: Field name, Value: CSS Selector

class ScrapeResponse(BaseModel):
    url: str
    data: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None
    
class DetectSelectorRequest(BaseModel):
    url: HttpUrl
    user_prompt: str
    
class DetectSelectorResponse(BaseModel):
    url: str
    selectors: Dict[str, str]
    success: bool = True
    error: Optional[str] = None