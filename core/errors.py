"""
Define custom error types for this project.
"""

from typing import Optional

# Errors with HTML scraping...
class ScraperError(Exception):
    """Base class for scraper-related exceptions."""
    def __init__(self, message: str, url: str = None, status_code: int = None):
        super().__init__(message)
        self.url = url
        self.status_code = status_code

    def __str__(self):
        base = super().__str__()
        if self.url:
            base += f" | URL: {self.url}"
        if self.status_code:
            base += f" | HTTP Status: {self.status_code}"
        return base

class PageNotFoundError(ScraperError):
    """Raised when the requested page does not exist (HTTP 404)."""
    pass

class DescriptionNotFoundError(ScraperError):
    """Raised when a page is found but no vehicle description is extracted."""
    pass

class RequestFailedError(ScraperError):
    """Raised for general HTTP errors (non-404)."""
    pass


# Errors with Config...
class ConfigError(Exception):
    """Raised when a required configuration (usually in .env) is missing or invalid."""

    def __init__(
        self,
        variable_name: str,
        message: str = None,
        extra_info: str = None
    ):
        """
        Args:
            variable_name: Name of the config variable.
            message: Optional custom message for the error.
            extra_info: Additional information to append to the error message.
        """
        if message is None:
            message = f"Missing or invalid configuration: {variable_name}. Please set it in your .env file."
        if extra_info:
            message += f" | {extra_info}"
        super().__init__(message)
        self.variable_name = variable_name
        self.extra_info = extra_info

    def __str__(self):
        return f"[CONFIG ERROR] {super().__str__()} | Variable: {self.variable_name}"
    
# Errors with LLM querying...
class LLMError(Exception):
    """Base exception for all LLM-related errors."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        self.provider = provider
        self.model = model
        self.original_exception = original_exception

        base_msg = message
        if provider:
            base_msg += f" | Provider: {provider}"
        if model:
            base_msg += f" | Model: {model}"
        if original_exception:
            base_msg += f" | Original Exception: {original_exception}"

        super().__init__(base_msg)


class LLMInitializationError(LLMError):
    """Raised when the LLM client fails to initialize."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        original_exception: Optional[Exception] = None,
        additional_message: Optional[str] = None
    ):
        message = "Failed to initialize LLM client"
        if additional_message:
            message += f": {additional_message}" 
        super().__init__(
            message=message,
            provider=provider,
            model=model,
            original_exception=original_exception,
        )


class LLMQueryError(LLMError):
    """Raised when a query to the LLM fails."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        additional_message: Optional[str] = None,
        original_exception: Exception = None,
    ):
        message = "LLM query failed"
        if additional_message:
            message += f": {additional_message}" 
        
        super().__init__(
            message=message,
            provider=provider,
            model=model,
            original_exception=original_exception,
        )


class LLMEmptyResponse(LLMError):
    """Raised when the LLM returns an empty response."""
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ):
        super().__init__(
            message="LLM returned an empty response",
            provider=provider,
            model=model,
        )