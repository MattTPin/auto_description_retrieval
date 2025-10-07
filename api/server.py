"""
Server to launch a FastAPI / Swagger UI instance with.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from client.llm_client import LLMClient
from core.main_functions.scrape_description import scrape_description
from core.errors import ScraperError

app = FastAPI(title="Auto Description Retrieval API", version="1.0")

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
    Retrieve and process a vehicle description from a Vehicle Detail Page (VDP) URL.

    This endpoint takes a VDP URL, fetches the associated page content, and uses
    an LLM-powered text isolation pipeline to extract a concise vehicle description.
    It returns both the extracted description and the number of tokens consumed
    during processing.

    ---
    ### Request Body
    - **vdp_url** (*str*):  
      The full URL of the Vehicle Detail Page to scrape and analyze.

    ### Responses
    - **200 OK**:  
      Successfully retrieved and processed the description.  
      Returns:
      ```json
      {
          "description": "2010 Subaru Outback 3.6R",
          "token_count": 185
      }
      ```
    - **400 Bad Request**:  
      Raised when the provided URL is invalid, inaccessible, or the scraper fails
      to extract a description.
    - **500 Internal Server Error**:  
      Returned if an unexpected error occurs during processing.

    ### Raises
    - **HTTPException(400)**: For known scraping or validation issues.
    - **HTTPException(500)**: For any unhandled or unexpected server errors.

    ### Example
    ```bash
    curl -X POST "https://api.example.com/scrape_description" \\
         -H "Content-Type: application/json" \\
         -d '{"vdp_url": "https://dealer.com/vehicle/123"}'
    ```

    Returns:
    ```json
    {
        "description": "2021 Toyota RAV4 XLE AWD",
        "token_count": 152
    }
    ```
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
