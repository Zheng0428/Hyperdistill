"""
Base class for LLM API providers.

Each provider encapsulates the differences in request parameters
and response parsing between different LLM API services.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class BaseProvider(ABC):
    """Abstract base class for all API providers.

    A Provider handles two concerns:
    1. Building provider-specific request parameters (e.g., extra_body).
    2. Extracting (content, thinking) from the API response object.
    """

    # Human-readable name for this provider
    name: str = "base"

    def build_request_params(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        timeout: int = 72000,
    ) -> Dict[str, Any]:
        """Build the full parameter dict for client.chat.completions.create().

        Subclasses should override `build_extra_body()` to add provider-specific
        params. This method assembles the complete kwargs.

        Args:
            messages: Chat messages.
            model: Model name.
            temperature: Sampling temperature.
            top_p: Nucleus sampling parameter.
            timeout: Request timeout in seconds.

        Returns:
            A dict of keyword arguments for the OpenAI API call.
        """
        params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "timeout": timeout,
        }

        if top_p is not None:
            params["top_p"] = top_p

        extra_body = self.build_extra_body()
        if extra_body:
            params["extra_body"] = extra_body

        return params

    @abstractmethod
    def build_extra_body(self) -> Optional[Dict[str, Any]]:
        """Return provider-specific extra_body dict, or None.

        Override this in subclasses for provider-specific parameters.
        """
        ...

    @abstractmethod
    def extract_response(self, response: Any) -> Tuple[str, Optional[str]]:
        """Extract (content, thinking) from the API response.

        Args:
            response: The raw response from client.chat.completions.create().

        Returns:
            A tuple of (content_text, thinking_text_or_None).
        """
        ...
