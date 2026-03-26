"""
DataLoader registry: auto-detect the appropriate loader by file extension.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from .base import BaseDataLoader
from .jsonl_loader import JsonlLoader
from .parquet_loader import ParquetLoader


class DataLoaderRegistry:
    """Registry that maps file extensions to DataLoader classes."""

    _loaders: Dict[str, Type[BaseDataLoader]] = {}

    @classmethod
    def register(cls, loader_class: Type[BaseDataLoader]) -> Type[BaseDataLoader]:
        """Register a loader class for its supported extensions.

        Can be used as a decorator:

            @DataLoaderRegistry.register
            class MyLoader(BaseDataLoader):
                ...
        """
        instance = loader_class.__new__(loader_class)
        for ext in instance.supported_extensions:
            cls._loaders[ext.lower()] = loader_class
        return loader_class

    @classmethod
    def get_loader_class(cls, file_path: str) -> Type[BaseDataLoader]:
        """Return the loader class for the given file path.

        Args:
            file_path: The data file path.

        Returns:
            The matching DataLoader class.

        Raises:
            ValueError: If no loader is registered for the file extension.
        """
        ext = Path(file_path).suffix.lower()
        if ext not in cls._loaders:
            supported = ", ".join(sorted(cls._loaders.keys()))
            raise ValueError(
                f"Unsupported file extension '{ext}'. Supported: {supported}"
            )
        return cls._loaders[ext]

    @classmethod
    def list_supported(cls) -> List[str]:
        """Return all supported file extensions."""
        return sorted(cls._loaders.keys())


# Register built-in loaders
DataLoaderRegistry.register(JsonlLoader)
DataLoaderRegistry.register(ParquetLoader)


def get_loader(
    file_path: str,
    required_fields: Optional[List[str]] = None,
    max_text_length: Optional[int] = None,
    text_field: str = "text",
    filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None,
) -> BaseDataLoader:
    """Convenience function: create a loader instance for the given file.

    Args:
        file_path: Path to the data file.
        required_fields: Only yield items containing all these fields.
        max_text_length: Skip items whose text_field exceeds this length.
        text_field: The field to check for length filtering.
        filter_fn: Custom filter function.

    Returns:
        A configured DataLoader instance.
    """
    loader_cls = DataLoaderRegistry.get_loader_class(file_path)
    return loader_cls(
        required_fields=required_fields,
        max_text_length=max_text_length,
        text_field=text_field,
        filter_fn=filter_fn,
    )
