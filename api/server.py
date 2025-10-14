"""
Server to launch a FastAPI / Swagger UI instance with.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from client.llm_client import LLMClient
from core.main_functions.scrape_description import scrape_description
from core.main_functions.determine_vpd_search_paths import determine_vpd_search_paths
from core.errors import ScraperError

app = FastAPI(title="Auto Description Retrieval API", version="1.0")

class SearchURLRequest(BaseModel):
    vdp_url: str

class SearchURLResponse(BaseModel):
    description: str
    token_count: int

@app.post(
    "/scrape_description",
    response_model=SearchURLResponse
)
def api_scrape_description(request: SearchURLRequest):
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
        return SearchURLResponse(
            description=description,
            token_count=token_count
        )
    except ScraperError as e:
        # Return a 400-level error for known scraper issues
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")



@app.post(
    "/determine_vpd_search_paths",
    response_model=SearchURLResponse
)
def api_determine_vpd_search_paths(request: SearchURLRequest):
    """
    Identify the most likely HTML search paths containing a vehicle description
    on a Vehicle Detail Page (VDP).

    This endpoint analyzes the provided VDP URL using an LLM-assisted pipeline
    to determine structured JSON search paths (HTML tag patterns) that can be
    used to locate the vehicle description section within the page’s source HTML.

    ---
    ### Request Body
    - **vdp_url** (*str*):  
      The full URL of the Vehicle Detail Page to analyze.

    ### Responses
    - **200 OK**:  
      Successfully analyzed the VDP and determined likely HTML search paths.  
      Returns:
      ```json
      {
          "search_paths": [
              [
                  {"tag": "div", "class": "dealer-comments dealer-comments--square"},
                  {"tag": "div", "class": "dealer-comments__text truncate-comments", "id": "dealer-comments"}
              ]
          ],
          "token_count": 240
      }
      ```
    - **400 Bad Request**:  
      Raised if the provided URL is invalid, inaccessible, or the LLM is unable
      to generate valid search paths.
    - **500 Internal Server Error**:  
      Returned if an unexpected error occurs during HTML retrieval or model inference.

    ### Raises
    - **HTTPException(400)**: For known validation, scraping, or parsing issues.
    - **HTTPException(500)**: For unhandled or unexpected server errors.

    ### Example
    ```bash
    curl -X POST "https://api.example.com/determine_vpd_search_paths" \\
         -H "Content-Type: application/json" \\
         -d '{"vdp_url": "https://dealer.com/vehicle/123"}'
    ```

    ### Example Response
    ```json
    {
        "search_paths": [
            [
                {"tag": "section", "class": "vehicle-details"},
                {"tag": "div", "class": "vehicle-description"}
            ]
        ],
        "token_count": 198
    }
    ```
    """
    try:
        llm_client = LLMClient()
        llm_client.test_connection()
        
        description, token_count = determine_vpd_search_paths(vdp_url=request.vdp_url, llm_client=llm_client)
        return SearchURLResponse(
            description=description,
            token_count=token_count
        )
    except ScraperError as e:
        # Return a 400-level error for known scraper issues
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
