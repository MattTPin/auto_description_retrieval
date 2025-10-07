from typing import Tuple
from client.llm_client import LLMClient
from core.helper_functions.fetch_vdp_html import fetch_vdp_html, determine_vdp_search_path
from core.helper_functions.isolate_vehicle_description import isolate_vehicle_description

def scrape_description(
    vdp_url: str,
    llm_client: LLMClient
) -> Tuple[str, int]:
    """
    Run the full HTML fetch and vehicle description isolation process.
    Args:
        vdp_url (str): The URL of the vehicle detail page to scrape.
        llm_client (LLMClient): An instance of the LLMClient used to process and isolate the vehicle description.
    Returns:
        Tuple[Optional[dict], int]: A tuple containing:
            - str: The isolated vehicle model description, or an error message if extraction fails.
            - int: The total number of tokens used in the LLM query.
    """
    # Determine which tags we'll be looking for in the HTML
    search_paths: list = determine_vdp_search_path(vdp_url=vdp_url)
    
    # Get the FULL vehicle description from the provided URL
    vdp_html: str = fetch_vdp_html(vdp_url=vdp_url, search_paths=search_paths)
    
    # Query the LLM to isolate ONLY the vehicle model description
    query_result, token_count = isolate_vehicle_description(
        prompt=vdp_html,
        llm_client=llm_client
    )

    description: str = (
        query_result.get("description")
        if isinstance(query_result, dict)
        else f"Failed to isolate vehicle description:\nFull LLM response {query_result}."
    )

    return description, token_count