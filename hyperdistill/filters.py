"""
Post-processing filters for distillation output.

Supports:
- Keyword filtering (remove AI model mentions from responses)
- Empty response removal
- Composable filter chains
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from .utils import log


# Default keywords to check for AI model mentions
DEFAULT_KEYWORDS = [
    "kimi", "claude", "chatgpt", "openai", "gemini", "deepseek",
    "moonshot", "anthropic", "gpt-4", "gpt4", "gpt-3.5", "gpt3.5",
    "qwen", "copilot", "tongyi", "wenxin", "ernie", "baichuan", "chatglm",
]


class BaseFilter:
    """Base class for output filters."""

    name: str = "base"

    def should_keep(self, item: Dict[str, Any]) -> bool:
        """Return True to keep the item, False to filter it out."""
        raise NotImplementedError

    def filter_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """Filter a JSONL file and write results to output.

        Args:
            input_path: Path to input JSONL file.
            output_path: Path to output file. If None, auto-generated.

        Returns:
            Path to the output file.
        """
        if output_path is None:
            if input_path.endswith(".jsonl"):
                output_path = input_path[:-6] + f".{self.name}.jsonl"
            else:
                output_path = input_path + f".{self.name}.jsonl"

        total = 0
        kept = 0
        errors = 0

        with open(input_path, "r", encoding="utf-8") as fin, \
             open(output_path, "w", encoding="utf-8") as fout:
            for line in fin:
                total += 1
                if total % 10000 == 0:
                    log(f"  Processed {total} lines...")

                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    errors += 1
                    continue

                if self.should_keep(item):
                    fout.write(line)
                    kept += 1

        print("=" * 60)
        print(f"Filter: {self.name}")
        print(f"Input:  {input_path}")
        print(f"Output: {output_path}")
        print(f"Total:  {total}")
        print(f"Kept:   {kept}")
        print(f"Removed: {total - kept - errors}")
        print(f"Errors: {errors}")
        print("=" * 60)

        return output_path


class KeywordFilter(BaseFilter):
    """Filter out items where response/thinking contain AI model keywords
    but query does not.

    Rules:
    1. If query has keywords -> keep (regardless of response/thinking)
    2. If query has no keywords but response/thinking has -> filter out
    3. If none have keywords -> keep
    """

    name = "keyword"

    def __init__(self, keywords: Optional[List[str]] = None):
        self.keywords = keywords or DEFAULT_KEYWORDS
        self._pattern = re.compile(
            r"\b(" + "|".join(re.escape(kw) for kw in self.keywords) + r")\b",
            re.IGNORECASE,
        )

    def _check_keywords(self, text: str) -> Set[str]:
        """Find all keyword matches in text."""
        if not text or not isinstance(text, str):
            return set()
        return {m.group(0).lower() for m in self._pattern.finditer(text)}

    def should_keep(self, item: Dict[str, Any]) -> bool:
        query_kw = self._check_keywords(item.get("query", ""))
        if query_kw:
            return True  # Query has keywords -> always keep

        response_kw = self._check_keywords(item.get("response", ""))
        thinking_kw = self._check_keywords(item.get("thinking", ""))

        if response_kw or thinking_kw:
            return False  # Response/thinking has keywords but query doesn't

        return True


class EmptyResponseFilter(BaseFilter):
    """Filter out items with empty or missing response field."""

    name = "empty_response"

    def __init__(self, response_field: str = "response"):
        self.response_field = response_field

    def should_keep(self, item: Dict[str, Any]) -> bool:
        response = item.get(self.response_field)
        return bool(response)


class FilterChain(BaseFilter):
    """Compose multiple filters into a chain. All must pass to keep."""

    name = "chain"

    def __init__(self, filters: List[BaseFilter]):
        self.filters = filters
        self.name = "+".join(f.name for f in filters)

    def should_keep(self, item: Dict[str, Any]) -> bool:
        return all(f.should_keep(item) for f in self.filters)


# Filter registry
FILTER_REGISTRY = {
    "keyword": KeywordFilter,
    "empty_response": EmptyResponseFilter,
}


def get_filter(name: str, **kwargs) -> BaseFilter:
    """Get a filter instance by name.

    Args:
        name: Filter name ('keyword', 'empty_response').
        **kwargs: Additional arguments for the filter constructor.

    Returns:
        A filter instance.
    """
    if name not in FILTER_REGISTRY:
        available = ", ".join(sorted(FILTER_REGISTRY.keys()))
        raise ValueError(f"Unknown filter '{name}'. Available: {available}")
    return FILTER_REGISTRY[name](**kwargs)
