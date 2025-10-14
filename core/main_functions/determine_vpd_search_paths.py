"""
Function to retrieve scrape HTML of a VDP page and then isolate the vehicle description using an
LLM query.
"""

import os
from dotenv import load_dotenv
from typing import Tuple
import ast

from client.llm_client import LLMClient
from client.scrape_html import scrape_html

from bs4 import BeautifulSoup, Tag

load_dotenv()
PRINT_DEBUG_COMMENTS = bool(os.getenv("PRINT_DEBUG_COMMENTS", False))


def determine_vpd_search_paths(vdp_url: str, llm_client: LLMClient) -> Tuple[str, int]:
    """
    Determine the most likely HTML components that contain a vehicle description
    on a dealership vehicle details page (VDP).

    This function:
      1. Scrapes the provided VDP URL for its HTML content.
      2. Extracts heading components from the HTML.
      3. Uses an LLM to identify which heading is most likely to mark
         the vehicle description section.
      4. Locates the parent div for that heading.
      5. Queries the LLM again to determine a JSON-structured search path
         to isolate the full description text.

    Args:
        vdp_url (str): URL of the vehicle details page to analyze.
        llm_client (LLMClient): Instance of the LLM client used to query the model.

    Returns:
        Tuple[str, int]:
            - A string describing the search paths or an error message.
            - The total token count used across both LLM queries.
    """
    # Scrape HTML and extract heading components
    full_html_soup: BeautifulSoup = scrape_html(url=vdp_url)
    extracted_headings = _extract_headings(full_html_soup.html)

    print("✅ Found the following headings in the HTML of the provided URL:\n")
    print(extracted_headings)
    print("\n-------------------------------------------")

    # Query the LLM to find the heading that likely denotes the vehicle description
    print("Querying LLM to identify vehicle description heading...\n")

    system_prompt_find_description_title = (
        "You are a helpful assistent for identifying HTML components. "
        "Look through the provided list of HTML headings components from the listing page "
        "for a single vehicle on a car dealership website."
        "Determine which is the most likely to contain a dealer-level description of the vehicle"
        "Respond ONLY with your context a valid JSON in this exact format...:\n"
        """
        {
            "tag" (str): "h2",
            "class" (str): "dealer-description__heading,
            "contents" (str): "Dealer Notes",
        }
        """
        "If no description can be found, return the json set `tag` to : `no_match`"
    )

    headings_search_result, token_count_1 = llm_client.query(
        system_prompt=system_prompt_find_description_title,
        user_prompt=extracted_headings,
        temperature=0.0,
        expect_json=True,
    )

    print("LLM returned potential description heading:\n")
    print(headings_search_result)
    print("\n-------------------------------------------")

    # If no valid match was found, exit early
    if not (
        isinstance(headings_search_result, dict)
        and "tag" in headings_search_result.keys()
        and headings_search_result["tag"] != "no_match"
    ):
        print("⚠️  No matching description heading found.\n")
        return "No dealer comments section found on webpage", token_count_1

    # Retrieve the parent div of the matched heading
    print("Extracting parent <div> of the identified heading...\n")
    parent_div_str = _get_parent_div_from_tag_dict(full_html_soup, headings_search_result)

    if not parent_div_str:
        return "Couldn't find match for heading serach result in original HTML" ,token_count_1

    print("Div containing description is:", parent_div_str)
    print("-------------------------------\n")

    # Query the LLM to determine the nested HTML path structure
    print("Querying LLM for final description component path...\n")
    system_prompt_find_full_description_div = (
        "You are a helpful assistant for identifying HTML components. "
        "You will be given an HTML div and its contents. "
        "Your task is to locate the components that contain the main vehicle description "
        "from a dealership website. "
        "Return a JSON list of lists, where each inner list represents a path of the nested HTML elements "
        "IN ORDER that identify the location of the description. "
        "Each element in the path should be a JSON object with the tag and relevant attributes "
        "(for example, 'tag', 'id', 'class'). "
        "Always return valid JSON list of dictionaries like this example: "
        """
        [
            {"tag": "div", "class": "dealer-comments dealer-comments--square"},
            {"tag": "div", "id": "dealer-comments", "class": "dealer-comments__text"}
        ]
        """
        "If no description can be found, return an empty JSON list: []"
    )

    determiend_search_paths, token_count_2 = llm_client.query(
        system_prompt=system_prompt_find_full_description_div,
        user_prompt=parent_div_str,
        temperature=0.0,
        expect_json=True,
    )

    # Return final result
    return determiend_search_paths, (token_count_1 + token_count_2)


def _extract_headings(html_soup: BeautifulSoup):
    """
    Extract all <h1>–<h6> elements including their text and return
    them as a list of strings (with opening and closing tags included).
    """
    headings = []
    for level in range(1, 7):  # h1 to h6
        for tag in html_soup.find_all(f"h{level}"):
            # Build a string with opening tag, text content, and closing tag
            attrs = " ".join(f'{k}="{v}"' for k, v in tag.attrs.items())
            if attrs:
                open_tag = f"<{tag.name} {attrs}>"
            else:
                open_tag = f"<{tag.name}>"
            headings.append(f"{open_tag}{tag.get_text(strip=True)}</{tag.name}>")
    return headings



def _get_parent_div_from_tag_dict(html_soup: BeautifulSoup, tag_dict: dict):
    """
    Given a BeautifulSoup object and a dictionary describing an HTML component,
    locate the first matching tag and return its parent <div> as a string.

    Example input:
        {
            "tag": "section",
            "class": "vehicle-images",
            "data-dlron-type": "vdpImagesBlockHoisin",
            "contents": "CONTENTS"
        }

    Behavior:
        - Uses the 'tag' key to determine which HTML tag to search for (e.g., 'div', 'section', etc.).
        - Treats any other keys (e.g., 'id', 'class', 'data-*', etc.) as HTML attributes to match.
        - If 'class' is a comma- or space-separated string, splits it into multiple class names.
        - If multiple tags match the attributes and 'contents' is provided, filters those
          whose visible text contains or equals the provided 'contents' (case-insensitive).
        - Returns the HTML string of the first matching parent <div>, or None if no match is found.

    Args:
        html_soup (BeautifulSoup): Parsed HTML to search through.
        tag_dict (dict): Dictionary describing the desired tag and attributes.

    Returns:
        str | None: HTML string of the parent <div> containing the match, or None if not found.
    """
    if not tag_dict:
        print("[DEBUG] No tag_dict provided.")
        return None

    tag_name = tag_dict.get("tag")
    contents_text = tag_dict.get("contents")

    if not tag_name:
        print("[DEBUG] No 'tag' key found in tag_dict.")
        return None

    # --- Build the attribute dictionary ---
    search_attrs = {}
    for key, value in tag_dict.items():
        # Skip non-HTML keys
        if key in {"tag", "contents"} or not value:
            continue

        # Handle multi-class strings like "widget-heading, h2" or "widget-heading h2"
        if key == "class":
            class_values = [cls.strip() for cls in value.replace(",", " ").split()]
            search_attrs["class"] = class_values
        else:
            # Treat all other keys as HTML attributes (e.g. id, data-*)
            search_attrs[key] = value

    # --- Find all tags that match ---
    matched_tags = html_soup.find_all(tag_name, attrs=search_attrs)
    print(f"[DEBUG] Searching for <{tag_name}> with {search_attrs}. Found {len(matched_tags)} matches.")

    if not matched_tags:
        print("[DEBUG] No tags found with given attributes.")
        return None

    # --- If multiple matches and 'contents' is given, narrow it down ---
    if len(matched_tags) > 1 and contents_text:
        contents_text_lower = contents_text.strip().lower()
        filtered = []
        for tag in matched_tags:
            tag_text = tag.get_text(strip=True).lower()
            if contents_text_lower in tag_text:
                filtered.append(tag)

        print(f"[DEBUG] Filtered {len(filtered)} matches based on contents='{contents_text}'.")
        matched_tags = filtered

    if not matched_tags:
        print("[DEBUG] No tags matched after contents filtering.")
        return None

    # --- Get the first matching tag ---
    matched_tag = matched_tags[0]

    # --- Find the nearest parent <div> ---
    parent_div = matched_tag.find_parent("div")
    if not parent_div:
        print("[DEBUG] No parent <div> found for matched tag.")
        return None

    print(f"[DEBUG] Found parent <div> for tag <{tag_name}>.")
    return str(parent_div)