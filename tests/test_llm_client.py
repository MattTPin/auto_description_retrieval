import os
import warnings
import pytest

from langchain_core.messages import AIMessage
from client.llm_client import LLMClient, SUPPORTED_PROVIDERS
from core.errors import ConfigError, LLMInitializationError, LLMQueryError, LLMEmptyResponse
from tests.test_variables import create_mock_llm_response


def is_env_defined(var_name: str) -> bool:
    """Check if env variable is defined and not placeholder."""
    value = os.getenv(var_name)
    if value is None or value == "<REPLACE_ME>":
        warnings.warn(f"{var_name} not set; skipping related tests")
        return False
    return True


# Test for the mock response function across providers and response types
@pytest.mark.parametrize("provider", ["anthropic", "openai", "mistral"])
@pytest.mark.parametrize("response_type", ["success", "failed", "unexpected_json", "not_json"])
def test_create_mock_llm_response(provider, response_type):
    """Ensure mock responses generate AIMessage with content and token info for all providers."""
    msg = create_mock_llm_response(
        function_name="isolate_vehicle_description",
        provider=provider,
        response_type=response_type,
    )

    # Validate type
    assert isinstance(msg, AIMessage)
    assert isinstance(msg.content, str)
    assert len(msg.content) > 0

    # Validate usage metadata
    usage = getattr(msg, "usage_metadata", {})
    assert usage.get("input_tokens", 0) > 0
    assert usage.get("output_tokens", 0) > 0
    assert usage.get("total_tokens", 0) == usage["input_tokens"] + usage["output_tokens"]

    # Validate response_metadata has provider-specific fields
    assert hasattr(msg, "response_metadata")
    metadata = getattr(msg, "response_metadata")
    assert metadata.get("usage", {}).get("total_tokens", 0) > 0
    assert "id" in metadata
    assert "model" in metadata


# Initialization Tests
@pytest.mark.parametrize("provider", SUPPORTED_PROVIDERS)
def test_init_invalid_values(provider):
    """Verify that invalid API key/model values raise ConfigError."""
    model_env = f"{provider.upper()}_MODEL_ID"
    key_env = f"{provider.upper()}_API_KEY"

    # Backup current env
    old_model = os.getenv(model_env)
    old_key = os.getenv(key_env)

    try:
        # Test missing key
        os.environ.pop(key_env, None)
        os.environ[model_env] = "some_model"
        with pytest.raises(ConfigError):
            LLMClient(provider=provider, test_mode=True)

        # Test placeholder key
        os.environ[key_env] = "<REPLACE_ME>"
        os.environ[model_env] = "some_model"
        with pytest.raises(ConfigError):
            LLMClient(provider=provider, test_mode=True)

        # Test placeholder model
        os.environ[key_env] = "some_key"
        os.environ[model_env] = "<REPLACE_ME>"
        with pytest.raises(ConfigError):
            LLMClient(provider=provider, test_mode=True)

    finally:
        # Restore env
        if old_model is not None:
            os.environ[model_env] = old_model
        if old_key is not None:
            os.environ[key_env] = old_key


# Test Mode Only: Skip providers without defined API keys in current .env
@pytest.mark.parametrize("provider", SUPPORTED_PROVIDERS)
def test_query_test_mode(provider):
    """Test query() in test_mode for all response types for providers with real API keys."""
    key_env = f"{provider.upper()}_API_KEY"
    model_env = f"{provider.upper()}_MODEL_ID"

    if not is_env_defined(key_env) or not is_env_defined(model_env):
        pytest.skip(f"{provider} API key/model not defined; skipping tests")

    for response_type in ["success", "failed", "unexpected_json", "not_json"]:
        client = LLMClient(
            provider=provider,
            function_name="isolate_vehicle_description",
            test_mode=True,
            test_response_type=response_type,
        )

        result, tokens = client.query(
            system_prompt="You are a vehicle description isolator.",
            user_prompt="Describe this Subaru.",
            expect_json=(response_type == "success"),
        )

        # Verify token count
        assert isinstance(tokens, int)
        assert tokens > 0

        if response_type == "success":
            assert isinstance(result, dict)
            assert "description" in result
        else:
            assert isinstance(result, str)


# Token Count Test
@pytest.mark.parametrize("provider", SUPPORTED_PROVIDERS)
def test_token_count(provider):
    """Ensure _get_token_usage returns int > 0 for test responses."""
    key_env = f"{provider.upper()}_API_KEY"
    model_env = f"{provider.upper()}_MODEL_ID"

    if not is_env_defined(key_env) or not is_env_defined(model_env):
        pytest.skip(f"{provider} API key/model not defined; skipping tests")

    client = LLMClient(
        provider=provider,
        function_name="isolate_vehicle_description",
        test_mode=True,
    )

    response = create_mock_llm_response(
        function_name="isolate_vehicle_description",
        provider=provider,
        response_type="success",
    )
    tokens = client._get_token_usage(response)
    assert isinstance(tokens, int)
    assert tokens > 0
