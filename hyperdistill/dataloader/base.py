"""
Base class for data loaders.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Iterator, List, Optional


class BaseDataLoader(ABC):
    """Abstract base class for all data loaders.

    A DataLoader reads raw data from a source file and yields individual
    data items as dictionaries using streaming iteration.
    It supports configurable filtering without loading everything into memory.
    """

    def __init__(
        self,
        required_fields: Optional[List[str]] = None,
        max_text_length: Optional[int] = None,
        text_field: str = "text",
        filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ):
        """
        Args:
            required_fields: If set, only yield items containing ALL these fields.
            max_text_length: If set, skip items whose `text_field` exceeds this length.
            text_field: The field name to check for max_text_length filtering.
            filter_fn: An optional custom filter function. Return True to keep.
        """
        self.required_fields = required_fields or []
        self.max_text_length = max_text_length
        self.text_field = text_field
        self.filter_fn = filter_fn

    def _passes_filters(self, item: Dict[str, Any]) -> bool:
        """Check if an item passes all configured filters."""
        # Required fields check
        for field in self.required_fields:
            if field not in item:
                return False

        # Max text length check
        if self.max_text_length is not None:
            text = item.get(self.text_field)
            if text and isinstance(text, str) and len(text) > self.max_text_length:
                return False

        # Custom filter
        if self.filter_fn is not None and not self.filter_fn(item):
            return False

        return True

    @abstractmethod
    def _iter_raw(self, file_path: str) -> Iterator[Dict[str, Any]]:
        """Iterate over raw data items from the source file (no filtering)."""
        ...

    def load(self, file_path: str) -> Iterator[Dict[str, Any]]:
        """Stream and yield filtered data items from the source file.

        This is the primary API. Uses streaming iteration — items are yielded
        one at a time without loading the full file into memory.

        Args:
            file_path: Path to the data file.

        Yields:
            Dict items that pass all filters.
        """
        for item in self._iter_raw(file_path):
            if self._passes_filters(item):
                yield item

    def load_all(self, file_path: str) -> List[Dict[str, Any]]:
        """Load all filtered items into a list (convenience method).

        WARNING: For large files, prefer `load()` which streams items.

        Args:
            file_path: Path to the data file.

        Returns:
            A list of filtered data items.
        """
        return list(self.load(file_path))

    def count_fast(self, file_path: str) -> int:
        """Fast approximate line count without parsing JSON.

        Subclasses can override this for format-specific fast counting.
        Falls back to raw line counting.

        Args:
            file_path: Path to the data file.

        Returns:
            Approximate total number of items in the file.
        """
        return self.count(file_path)

    @abstractmethod
    def count(self, file_path: str) -> int:
        """Count the number of valid (filtered) items.

        Args:
            file_path: Path to the data file.

        Returns:
            The count of items that pass filters.
        """
        ...

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Return supported file extensions (e.g., ['.jsonl'])."""
        ...
