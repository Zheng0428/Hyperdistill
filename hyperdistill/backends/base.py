"""
Base class for execution backends.

A Backend encapsulates "how to call an LLM" — whether through
an OpenAI-compatible API or a CLI subprocess (e.g., claude).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from ..tasks.base import BaseTask


class BaseBackend(ABC):
    """Abstract base class for all execution backends.

    A Backend takes a data item + task, invokes the LLM in some way,
    and returns (content, thinking).
    """

    name: str = "base"

    @abstractmethod
    async def call(
        self,
        item: Dict[str, Any],
        task: BaseTask,
    ) -> Tuple[str, Optional[str]]:
        """Call the LLM backend to generate content.

        Args:
            item: The data item to process.
            task: The task instance (provides build_messages, etc.).

        Returns:
            A tuple of (content_text, thinking_text_or_None).

        Raises:
            Exception: On any failure (caller handles retries).
        """
        ...
