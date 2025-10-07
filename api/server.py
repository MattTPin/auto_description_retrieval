"""
Server to launch a FastAPI / Swagger UI instance with.

Launch with 
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from client.llm_client import LLMClient
from core.main_functions.scrape_description import scrape_description
from core.errors import ScraperError

app = FastAPI(title="Auto Description Retrieval API", version="1.0")

# Initialize the LLM client once at startup



class ScrapeDescriptionRequest(BaseModel):
    vdp_url: str

class ScrapeDescriptionResponse(BaseModel):
    description: str
    token_count: int

@app.post(
    "/scrape_description",
    response_model=ScrapeDescriptionResponse
)
def api_scrape_description(request: ScrapeDescriptionRequest):
    """
    Fetch and process a vehicle description from a VDP URL.
    """
    try:
        llm_client = LLMClient()
        llm_client.test_connection()
        
        description, token_count = scrape_description(vdp_url=request.vdp_url, llm_client=llm_client)
        return ScrapeDescriptionResponse(
            description=description,
            token_count=token_count
        )
    except ScraperError as e:
        # Return a 400-level error for known scraper issues
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
