"""
Used to scrape a vdp_html with specific details about a vehicle.
"""

import re
from typing import List, Any, Dict
from urllib.parse import urlparse

from client.scrape_html import scrape_html
from core.errors import (
    ScraperError,
)

from typing import List, Dict, Any

def fetch_vdp_html(vdp_url: str, search_paths: List[List[Dict[str, Any]]]) -> str:
    """
    Retrieve the vehicle description HTML using flexible, nested search definitions.

    Args:
        vdp_url (str): The URL of the vehicle details page.
        search_paths (List[List[Dict[str, Any]]], optional): 
            A list of search chains. Each chain is a list of dicts defining nested tag lookups, e.g.:

            [
                [  # first possible chain
                    {"tag": "div", "id": "vehicle-description"},
                    {"tag": "div", "class_": "description"},
                ],
                [  # fallback chain
                    {"tag": "section", "id": "details"},
                ]
            ]

    Returns:
        str: Extracted and cleaned description text.

    Raises:
        ScraperError: If no valid description section could be found.
    """
    soup = scrape_html(vdp_url)

    attempted_paths = []

    for chain in search_paths:
        current_element = soup
        last_found = None
        chain_repr = " > ".join(
            [f"{d['tag']}({', '.join(f'{k}={v}' for k,v in d.items() if k!='tag')})" for d in chain]
        )
        attempted_paths.append(chain_repr)

        for level in chain:
            tag = level.get("tag")
            attrs = {k: v for k, v in level.items() if k != "tag"}
            next_element = current_element.find(tag, **attrs)

            if not next_element:
                # Stop descending; use the last successfully found element as fallback
                break
            last_found = next_element
            current_element = next_element

        if last_found:
            text = last_found.get_text(separator=" ", strip=True)
            text = _remove_dealership_marketing_paragraph(text)
            return text

    # If we reach this point, no path matched
    raise ScraperError(
        message=(
            f"Could not find description section using provided tag search paths.\n"
            f"Tried the following chains (outermost to innermost):\n"
            + "\n".join(f"  - {p}" for p in attempted_paths)
        ),
        url=vdp_url,
    )


def determine_vdp_search_path(vdp_url: str) -> List[List[Dict[str, Any]]]:
    """
    Determine which search path to use based on the provided VDP URL.

    Args:
        vdp_url (str): The full vehicle details page URL.

    Returns:
        List[List[Dict[str, Any]]]: The appropriate search path for the URL.

    Raises:
        ScraperError: If no matching pattern is found for the given URL.
    """

    # Known site patterns mapped to search paths
    search_paths_by_domain = {
        "greghublerford.com": [
            [
                {"tag": "div", "id": "vehicle-description"},
                {"tag": "div", "class_": "description"},
            ]
        ],
        "sftoyota.com": [
            [
                {"tag": "div", "class": "dealer-comments dealer-comments--square"},
                {"tag": "div", "id": "dealer-comments", "class": "dealer-comments__text"},
            ]
        ],
        "bergeronchryslerjeep.com": [
            [
                {"tag": "div", "id": "dealernotes1-app-root"},
                {"tag": "div", "class": "content"},
            ]
        ],
    }

    parsed = urlparse(vdp_url)
    normalized_url = f"{parsed.netloc}{parsed.path}".lower()

    for pattern, search_path in search_paths_by_domain.items():
        if pattern.lower() in normalized_url:
            return search_path

    # No match found
    raise ScraperError(
        message=(
            f"No matching search path pattern found for URL: {vdp_url}\n"
            f"Checked patterns: {list(search_paths_by_domain.keys())}"
        ),
        url=vdp_url,
    )


def _remove_dealership_marketing_paragraph(text: str) -> str:
    """
    Removes dealership marketing paragraphs from the text if found.

    Searches for a paragraph that begins with a known marketing sentence and
    removes it up to the next break, newline, or period. Falls back to end of
    text if no such marker is found.

    Args:
        text (str): The full vehicle description text.

    Returns:
        str: The cleaned text with marketing content removed.
    """
    start_pattern = re.compile(
        r"Introducing the All New Greg Hubler Promise:",
        flags=re.IGNORECASE
    )
    match = start_pattern.search(text)
    if not match:
        return text

    start_index = match.start()
    break_match = re.search(r"(?:<br\s*/?>|\n)", text[start_index:], flags=re.IGNORECASE)
    end_index = None

    if break_match:
        end_index = start_index + break_match.end()
    else:
        period_match = re.search(r"\.", text[start_index:])
        end_index = start_index + period_match.end() if period_match else len(text)

    cleaned_text = text[:start_index] + text[end_index:]
    cleaned_text = re.sub(r"\s{2,}", " ", cleaned_text).strip()

    return cleaned_text