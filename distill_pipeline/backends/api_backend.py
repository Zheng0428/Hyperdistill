"""
API Backend — calls LLM via AsyncOpenAI /chat/completions.

This is the original execution path, extracted from engine.py
into a Backend for modularity.
"""

from typing import Any, Dict, Optional, Tuple

from .base import BaseBackend
from ..client_pool import ClientPool
from ..providers.base import BaseProvider
from ..tasks.base import BaseTask


class ApiBackend(BaseBackend):
    """Backend that calls LLM via OpenAI-compatible API."""

    name = "api"

    def __init__(
        self,
        client_pool: ClientPool,
        provider: BaseProvider,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        timeout: int = 72000,
    ):
        """
        Args:
            client_pool: Pool of AsyncOpenAI clients.
            provider: Provider for request params and response parsing.
            temperature: Sampling temperature.
            top_p: Nucleus sampling parameter.
            timeout: Request timeout in seconds.
        """
        self.client_pool = client_pool
        self.provider = provider
        self.temperature = temperature
        self.top_p = top_p
        self.timeout = timeout

    async def call(
        self,
        item: Dict[str, Any],
        task: BaseTask,
    ) -> Tuple[str, Optional[str]]:
        """Call the LLM via AsyncOpenAI API.

        Steps:
        1. Hot-reload config if needed
        2. Get a random client from the pool
        3. Build messages via task.build_messages()
        4. Build request params via provider.build_request_params()
        5. Call client.chat.completions.create()
        6. Extract (content, thinking) via provider.extract_response()
        """
        # Hot-reload check
        self.client_pool.reload_if_needed()

        # Get client
        client, config = self.client_pool.get_random()
        model = config.get("model", "gpt-4")

        # Build messages from task
        messages = task.build_messages(item)

        # Build request params from provider
        params = self.provider.build_request_params(
            messages=messages,
            model=model,
            temperature=self.temperature,
            top_p=self.top_p,
            timeout=self.timeout,
        )

        # Call the API
        response = await client.chat.completions.create(**params)

        # Extract response using provider
        return self.provider.extract_response(response)
