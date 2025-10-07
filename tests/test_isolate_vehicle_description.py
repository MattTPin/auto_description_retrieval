import pytest
from unittest.mock import Mock
import warnings

from client.llm_client import LLMClient
from core.helper_functions.isolate_vehicle_description import isolate_vehicle_description
from core.errors import LLMQueryError

from tests.test_variables import (
    expected_test_responses
)

# Helper function to create a fresh mock client
def create_mock_llm_client(response_type="success") -> LLMClient:
    """
    Returns a fresh mock LLMClient in test mode.
    """
    client = LLMClient.__new__(LLMClient)  # bypass __init__
    client.provider = "anthropic"
    client.model = "claude-3-haiku-20240307"
    client.api_key = "dummy"
    client.client = True  # pretend the client is initialized
    client.test_mode = True
    client.function_name = "isolate_vehicle_description"
    client.test_response_type = response_type
    client.fallback_message = "No description found"

    # Mock the __call__ or send_message used by isolate_vehicle_description
    if response_type == "success":
        content = '{"description": "Take on any road with confidence"}'
    elif response_type == "failed":
        content = '{"description": "No description found"}'
    elif response_type == "unexpected_json":
        content = '{"vehicle_info": "Some raw info"}'  # missing "description"
    elif response_type == "not_json":
        content = "Plain text, not JSON"
    else:
        content = '{"description": "No description found"}'

    mock_response = {
        "content": content,
        "response_metadata": {},
    }

    # Assume isolate_vehicle_description calls the client instance directly
    client.__call__ = Mock(return_value=mock_response)
    return client



@pytest.mark.parametrize("response_type", ["success", "failed"])
def test_isolate_vehicle_description_success_and_failed(response_type):
    """
    Test isolate_vehicle_description for both 'success' and 'failed' simulated responses.
    Pulls expected descriptions from expected_test_responses.
    """
    mock_client = create_mock_llm_client(response_type)
    result, token_count = isolate_vehicle_description(
        "Sample vehicle text",
        mock_client,
        test_mode=True
    )

    expected_description = expected_test_responses["isolate_vehicle_description"][response_type]["description"]

    assert isinstance(result, dict)
    assert isinstance(token_count, int)
    assert "description" in result
    assert result["description"] == expected_description


def test_isolate_vehicle_description_unexpected_json():
    """
    Test isolate_vehicle_description with unexpected JSON structure.
    Should still return a dict with a fallback description if missing.
    """
    mock_client = create_mock_llm_client("unexpected_json")
    result, token_count = isolate_vehicle_description(
        "Random vehicle text",
        mock_client,
        test_mode=True
    )

    assert isinstance(result, dict)
    assert isinstance(token_count, int)
    assert "description" in result
    # Since description is missing in JSON, fallback should be used
    assert result["description"] == "No description found"
    # Original keys may still exist
    assert "vehicle_info" in result


def test_isolate_vehicle_description_not_json_warns(monkeypatch):
    """
    Test isolate_vehicle_description when model returns plain text instead of JSON.
    The function should normalize it into a dict with 'description' key.
    """
    mock_client = create_mock_llm_client("not_json")

    # Patch warnings.warn to capture warning instead of printing
    warnings_called = {}
    def fake_warn(msg, category=None, **kwargs):
        warnings_called["msg"] = msg
        warnings_called["category"] = category
    monkeypatch.setattr("warnings.warn", fake_warn)

    result, token_count = isolate_vehicle_description(
        "Random vehicle text",
        mock_client,
        test_mode=True
    )

    assert isinstance(result, dict)
    assert "description" in result
    assert isinstance(result["description"], str)
    assert isinstance(token_count, int)
    # Ensure warning was triggered
    assert "LLM did not return valid JSON" in warnings_called["msg"]
    assert warnings_called["category"] == UserWarning
