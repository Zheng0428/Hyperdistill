"""
JSONL file data loader with streaming support.
"""

import json
import os
from typing import Any, Dict, Iterator, List

from .base import BaseDataLoader
from ..utils import log


class JsonlLoader(BaseDataLoader):
    """Load data from JSONL (JSON Lines) files.

    Each line in the file should be a valid JSON object.
    Blank lines and JSON decode errors are silently skipped.
    Uses streaming iteration — never loads the full file into memory.
    """

    @property
    def supported_extensions(self) -> List[str]:
        return [".jsonl"]

    def _iter_raw(self, file_path: str) -> Iterator[Dict[str, Any]]:
        """Stream JSON objects from the JSONL file one at a time."""
        file_size = os.path.getsize(file_path)
        size_mb = file_size / (1024 * 1024)
        log(f"Streaming JSONL: {file_path} ({size_mb:.1f} MB)")

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    if isinstance(item, dict):
                        yield item
                except json.JSONDecodeError:
                    continue

    def count(self, file_path: str) -> int:
        """Count filtered items in the JSONL file (streams, no full load)."""
        total = 0
        for _ in self.load(file_path):
            total += 1
        return total

    def count_fast(self, file_path: str) -> int:
        """Fast line count without parsing JSON — just counts non-blank lines."""
        total = 0
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    total += 1
        return total
