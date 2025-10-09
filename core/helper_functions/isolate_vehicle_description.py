"""
Functions to trim a full description including dealership and features down to only a key description of the vehicle.
"""

from client.llm_client import LLMClient
from typing import Optional, Tuple

def isolate_vehicle_description(
    prompt: str,
    llm_client: Optional[LLMClient] = None,
    test_mode: bool = False
) -> Tuple[Optional[dict], int]:
    """
    Takes provided text and queries the LLM to identify and isolate a vehicle description
    from a dealership's full listing (dealer information, feature breakdown, etc.).

    Args:
        prompt (str): The FULL dealership text to analyze and summarize.
        llm_client (Optional[LLMClient]): A pre-initialized LLMClient instance to query with.
        test_mode (bool): Whether to use mock/test responses instead of a real LLM call.

    Returns:
        Tuple[Optional[dict], int]: A tuple containing:
            - dict or None: The isolated vehicle description, or None if parsing fails.
            - int: The total number of tokens used in the LLM query.

    Raises:
        LLMQueryError: If the LLM call or response parsing fails.
        LLMEmptyResponse: If the LLM returns no content.
    """
    # If existing LLM client not provided then initiate a connection to one
    function_name = "isolate_vehicle_description"
    fallback_message = "No description found."

    # If an existing client is provided, create a copy with overrides for this funciton
    if llm_client:
        llm_client = llm_client.clone_with_overrides(
            test_mode=test_mode,
            function_name=function_name,
            fallback_message=fallback_message,
        )
    else:
        # Create new LLMClient entirely
        llm_client = LLMClient(
            test_mode=test_mode,
            function_name=function_name,
            fallback_message=fallback_message,
        )
        llm_client.test_connection()

    # Description extraction prompt
    system_prompt: str = (
        "You are a vehicle description isolation assistant. "
        "You will receive text copied from a dealership listing containing dealer info, features, etc. "
        "Your will extract only the vehicle's descriptive text verbatim — no summaries or added text. "
        "The description may appear in one or multiple paragraphs, including in natural-language sections like reviews. "
        "You may include multiple descriptive paragraphs. "
        "Respond ONLY with your context a valid JSON in this exact format...:\n"
        """
        {"description" (str): "VEHICLE MODEL DESCRIPTION"}
        """
        "IMPORTANT: If the description contains quotation marks (\") or single quotes ('), "
        "escape double quotes with a backslash (\\\") so the JSON remains valid. "
        "If no description can be found, return the json set `description` to : `" + fallback_message + "`"
    )
    
    result, token_count = llm_client.query(
        system_prompt=system_prompt,
        user_prompt=prompt,
        temperature=0.0, # Minimal temperature to minimize randomness
        expect_json=True,
    )
    
    # Normalize everything into a dict with a 'description' key
    if isinstance(result, str):
        description = result.strip() or fallback_message
        result = {"description": description}
    elif isinstance(result, dict):
        description = (result.get("description") or "").strip()
        if not description:
            result["description"] = fallback_message
    else:
        result = {"description": fallback_message}
    
    return result, token_count