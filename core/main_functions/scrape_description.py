"""
Function to retrieve scrape HTML of a VDP page and then isolate the vehicle description using an
LLM query.
"""

from typing import Tuple, Optional

from client.llm_client import LLMClient
from core.helper_functions.fetch_vdp_html import fetch_vdp_html, determine_vdp_search_path
from core.helper_functions.isolate_vehicle_description import isolate_vehicle_description


def scrape_description(
    vdp_url: str,
    llm_client: LLMClient,
    print_debug_comments: Optional[bool] = False
) -> Tuple[str, int]:
    """
    Run the full HTML fetch and vehicle description isolation process.
    Args:
        vdp_url (str): The URL of the vehicle detail page to scrape.
        llm_client (LLMClient): An instance of the LLMClient used to process and isolate the vehicle description.
        print_debug_comments (bool): Show full text from the dealer
    Returns:
        Tuple[Optional[dict], int]: A tuple containing:
            - str: The isolated vehicle model description, or an error message if extraction fails.
            - int: The total number of tokens used in the LLM query.
    """
    # Look at the URL to determine where in HTML description is stored (known locations)
    search_paths: list = determine_vdp_search_path(vdp_url=vdp_url)
    
    # Get the FULL "dealer notes" text from the provided URL
    full_notes_text: str = fetch_vdp_html(vdp_url=vdp_url, search_paths=search_paths)
    
    if print_debug_comments:
        print(
            f"--- FULL DEALER NOTES TEXT ---\n",
            full_notes_text,
            "\n----------------------------------------------------------------\n"
        )
    
    # Query the LLM to isolate ONLY the vehicle model description
    query_result, token_count = isolate_vehicle_description(
        prompt=full_notes_text,
        llm_client=llm_client
    )

    # Return description
    description: str = (
        query_result.get("description")
        if isinstance(query_result, dict)
        else f"Failed to isolate vehicle description:\nFull LLM response {query_result}."
    )

    return description, token_count