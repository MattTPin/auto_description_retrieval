"""
llm_client.py

Universal LangChain-based client for multiple LLM providers.
Supports Anthropic (Claude), OpenAI, and Mistral.
Includes configuration validation, flexible prompting, and optional JSON parsing.
"""
import json
import os
import tiktoken
from typing import Optional, Any, Dict, Literal
import warnings

from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain.schema import AIMessage, SystemMessage, HumanMessage

from core.errors import (
    ConfigError,
    LLMError,
    LLMInitializationError,
    LLMQueryError,
    LLMEmptyResponse
)
from tests.test_variables import (
    create_mock_llm_response
)

SUPPORTED_PROVIDERS = ["anthropic", "openai", "mistral"]
load_dotenv()

class LLMClient:
    """
    A flexible LLM client supporting multiple providers via LangChain.
    """
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        function_name: Optional[str] = None,
        fallback_message: Optional[str] = None,
        test_mode: Optional[bool] = False,
        test_response_type: Literal["success", "failed", "unexpected_json", "not_json"] = "success",
    ) -> None:
        """Initialize the client and resolve provider-specific configuration."""
        # General variablews
        self.function_name = function_name
        self.fallback_message = fallback_message
        
        # Testing variables
        self.test_mode = test_mode
        self.test_response_type = test_response_type

        # Model select variables
        self.provider: Optional[str] = (provider or os.getenv("LLM_PROVIDER", "")).strip().lower()
        self.model: Optional[str] = model
        self.api_key: Optional[str] = None

        if self.provider not in SUPPORTED_PROVIDERS:
            raise ConfigError(
                variable_name="LLM_PROVIDER",
                extra_info=f"Choices are: {SUPPORTED_PROVIDERS}"
            )

        # Map provider to env variable names for model and API key
        env_map = {
            "anthropic": ("ANTHROPIC_MODEL_ID", "ANTHROPIC_API_KEY"),
            "openai": ("OPENAI_MODEL_ID", "OPENAI_API_KEY"),
            "mistral": ("MISTRAL_MODEL_ID", "MISTRAL_API_KEY"),
        }
        model_env, api_key_env = env_map[self.provider]
        # Use default model for the provider if not specified
        if not self.model:
            self.model = os.getenv(model_env)
        # Retrieve the provider specific API key
        self.api_key = os.getenv(api_key_env)

        # Raise errors if no api key or model specified
        if not self.api_key or self.api_key == "<REPLACE_ME>":
            raise ConfigError(
                variable_name=f"{self.provider}_API_KEY",
                message=(
                    f"You must set a `{self.provider}` API key in your env variables in order "
                    "to run LLM queries to their services."
                )
            )
        if not self.model or self.model == "<REPLACE_ME>":
            raise ConfigError(
                variable_name=f"{self.provider}_MODEL_ID",
                message=(
                    f"You must set a `{self.provider}` default model in your env variables "
                    "OR provide an explicit model name while initating the LLMClient "
                    "in order to run LLM queries to their services."
                )
            )

        # Confirm that we can initiate the model
        try:
            self.client = init_chat_model(
                model=self.model,
                api_key=self.api_key,
                temperature=0.5,
            )
        except Exception as e:
            raise LLMInitializationError(
                provider=self.provider,
                model=self.model,
                original_exception=e
            )

    def _default_model_for_provider(self) -> str:
        """Provide a fallback model per provider."""
        defaults = {
            "anthropic": "claude-3-sonnet-20240229",
            "openai": "gpt-4o-mini",
            "mistral": "mistral-small-latest",
        }
        return defaults.get(self.provider, "")
    
    def clone_with_overrides(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        function_name: Optional[str] = None,
        fallback_message: Optional[str] = None,
        test_mode: Optional[bool] = None,
        test_response_type: Optional[str] = None,
    ) -> "LLMClient":
        """
        Return a shallow clone of this client with optional overrides.
        Any argument set to None will use the current value from self.
        """
        return LLMClient(
            provider=provider if provider is not None else self.provider,
            model=model if model is not None else self.model,
            function_name=function_name if function_name is not None else self.function_name,
            fallback_message=fallback_message if fallback_message is not None else self.fallback_message,
            test_mode=test_mode if test_mode is not None else self.test_mode,
            test_response_type=test_response_type if test_response_type is not None else self.test_response_type,
        )

    # --- CONFIG VALIDATION HELPERS ---

    def _test_anthropic_config(self) -> bool:
        """Validate Anthropic connection."""
        return self._test_connection_generic("Anthropic")

    def _test_openai_config(self) -> bool:
        """Validate OpenAI connection."""
        return self._test_connection_generic("OpenAI")

    def _test_mistral_config(self) -> bool:
        """Validate Mistral connection."""
        return self._test_connection_generic("Mistral")

    def _test_connection_generic(self, provider_name: str) -> bool:
        """Generic connection test used by all providers."""
        if not self.client:
            raise LLMInitializationError(
                provider=provider_name,
                model=self.model,
                original_exception="No client initialized"
            )
        try:
            response = self.client.invoke("ping")
            if response and hasattr(response, "content"):
                return True
        except Exception as e:
            additional_message = ""
            if "insufficient_quota" in str(e).lower():
                additional_message += f"Out of tokens for `{provider_name}`"
            if "rate limit" in str(e).lower():
                additional_message += f"Rate limit reached for `{provider_name}`"
            raise LLMInitializationError(
                provider=provider_name,
                model=self.model,
                original_exception=e,
                additional_message=additional_message
            )
        return False

    def test_connection(self) -> bool:
        """
        Run provider-specific connection validation.
        Returns True if successful, False otherwise.
        """
        if self.provider == "anthropic":
            return self._test_anthropic_config()
        elif self.provider == "openai":
            return self._test_openai_config()
        elif self.provider == "mistral":
            return self._test_mistral_config()
    
        raise LLMInitializationError(
            provider=self.provider,
            model=self.model,
            original_exception="No valid provider selected"
        )
    

    # --- QUERY EXECUTION ---

    def query(
        self,
        system_prompt: Optional[str],
        user_prompt: str,
        temperature: float = 0.5,
        expect_json: bool = False,
    ) -> str | dict:
        """
        Perform a model query with flexible configuration.

        Args:
            system_prompt (Optional[str]): Instruction or behavioral setup for the model.
            user_prompt (str): Input text or main query.
            temperature (float): Model creativity level (0.0–1.0).
            expect_json (bool): Whether to parse response as JSON.

        Returns:
            str | dict: dict if `expect_json` is True otherwise str. str may be returned even
                when `expect_json` is True if the LLM does not behave as expected.l
        """
        # Keep track of how many tokens were used
        token_count: int = 0
        
        if not self.client:
            raise LLMInitializationError(provider=self.provider, model=self.model)

        messages = [
            SystemMessage(content=system_prompt) if system_prompt else None,
            HumanMessage(content=user_prompt)
        ]
        messages = [m for m in messages if m]  # Remove None

        try:
            if self.test_mode == False:
                # Query the LLM
                response: AIMessage = self.client.invoke(
                    messages,
                    temperature=temperature
                )
                
            elif self.function_name and self.test_response_type:
                # Return a mock LLM response (for testing)
                response: AIMessage = create_mock_llm_response(
                    function_name=self.function_name,
                    response_type=self.test_response_type,
                    provider=self.provider
                )
            else:
                # Raise incorrect test config error
                raise LLMQueryError(
                    provider=self.provider,
                    model=self.model,
                    additional_message= (
                        "Test mode is enabled without valid test variables having been defined. "
                        f"self.test_mode = {self.test_mode} "
                        f"self.function_name = {self.function_name} "
                    ),
                )
            
            # Raise error if no response
            if not response or not response.content:
                raise LLMEmptyResponse(provider=self.provider, model=self.model)
            
            # Count tokens
            token_count = self._get_token_usage(response)
            
            # Get the result text
            result_text = response.content.strip()
            if expect_json:
                try:
                    # Normalize escaped quotes
                    safe_text = result_text.replace('\\"', '"').strip()

                    # Remove Markdown JSON fences like ```json ... ``` or ```
                    if safe_text.startswith("```"):
                        # Remove leading and trailing code fences safely
                        safe_text = safe_text.strip("`")
                        # Remove possible language tag (like 'json')
                        safe_text = safe_text.replace("json\n", "", 1).replace("json\r\n", "", 1)
                        # Remove any trailing triple backticks
                        safe_text = safe_text.strip("`").strip()

                    # Attempt to parse cleaned JSON
                    result_text = json.loads(safe_text)
                except Exception as e:
                    # Warn the user if we're expecting a json response but didn't get one (LLM faliure)
                    warnings.warn(
                        (
                            f"LLM did not return valid JSON when it was expected to.\n"
                            f"Exception: `{e}`\n"
                            f"Provider: {self.provider}\n"
                            f"Model: {self.model}\n"
                            f"Function: {self.function_name}\n"
                            "This may occur if the LLM output was malformed or test mode variables "
                            "were not correctly defined."
                        ),
                        category=UserWarning,
                    )
            
            # Return fallback message if result text is empty
            if not result_text:
                result_text = self.fallback_message or "No query result"

            return result_text, token_count

        except Exception as e:
            raise LLMQueryError(provider=self.provider, model=self.model, original_exception=e)
    
    
    def _get_token_usage(self, response: Any) -> int:
        """
        Retrieve or estimate the total number of tokens used in a model response.
        """
        # Direct usage attribute
        if hasattr(response, "usage") and isinstance(response.usage, dict):
            return int(response.usage.get("total_tokens", 0))

        # response_metadata["usage"] (Anthropic / OpenAI / Mistral)
        if hasattr(response, "response_metadata"):
            metadata = getattr(response, "response_metadata", {})
            usage = metadata.get("usage", {})
            if usage:
                # Some providers put total_tokens under 'total_tokens'
                return int(usage.get("total_tokens", usage.get("input_tokens", 0) + usage.get("output_tokens", 0)))

        # usage_metadata
        if hasattr(response, "usage_metadata"):
            usage = getattr(response, "usage_metadata", {})
            if usage:
                return int(usage.get("total_tokens", usage.get("input_tokens", 0) + usage.get("output_tokens", 0)))

        # fallback metadata["token_usage"]
        if hasattr(response, "metadata"):
            metadata = getattr(response, "metadata", {})
            usage = metadata.get("token_usage", {})
            if usage:
                return int(usage.get("total_tokens", usage.get("total", 0)))

        # fallback: estimate from content text
        text = getattr(response, "content", "") or ""
        if not text:
            return 0

        try:
            # Final fallback: Use tiktoken package to count tokens
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except Exception:
            return len(text.split())