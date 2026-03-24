"""
Base class for distillation tasks.

A Task defines how to:
1. Identify items (for dedup/resume).
2. Build chat messages from a data item.
3. Process the API response back into the data item.
4. Validate whether an item should be processed.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseTask(ABC):
    """Abstract base class for all distillation tasks."""

    # Human-readable name for this task
    name: str = "base"

    @abstractmethod
    def get_id(self, item: Dict[str, Any]) -> str:
        """Return a unique ID for the given item, used for dedup/resume.

        Args:
            item: A data item dict.

        Returns:
            A string ID. Items with the same ID are considered duplicates.
        """
        ...

    @abstractmethod
    def build_messages(self, item: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build chat messages (system + user) from a data item.

        Args:
            item: A data item dict.

        Returns:
            A list of message dicts with 'role' and 'content' keys.
        """
        ...

    @abstractmethod
    def process_result(
        self,
        item: Dict[str, Any],
        content: str,
        thinking: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Merge the API response into the data item.

        Args:
            item: The original data item dict.
            content: The response content from the API.
            thinking: The thinking/reasoning content, if available.

        Returns:
            The enriched item dict, or None if the result is invalid.
        """
        ...

    @abstractmethod
    def validate_item(self, item: Dict[str, Any]) -> bool:
        """Check if a data item is valid for processing.

        Args:
            item: A data item dict.

        Returns:
            True if the item should be processed, False to skip.
        """
        ...

    def get_id_field(self) -> Optional[str]:
        """Return the field name used as the ID source, or None if computed.

        This helps the OutputWriter know which field to check for resume.
        """
        return None

    def expand_items(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Expand a single input item into multiple processing items.

        Override this method if your task needs to create multiple processing
        items from a single input item (e.g., multi-turn conversations where
        each turn is processed separately, or generating multiple variations).

        Each expanded item MUST have a unique ID via get_id() for proper
        deduplication and resume support.

        Default implementation: no expansion (returns [item]).

        Args:
            item: A single input data item.

        Returns:
            A list of items to process. Each item should be processable by
            build_messages() and process_result().
        """
        return [item]
