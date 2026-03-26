"""
API configuration loading and management.

Supports two config formats:
  - New format: each API object has a 'concurrency' field
  - Old format: a separate 'api_concurrencies' array at root level
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .utils import log


def load_config(config_path: str) -> Tuple[List[Dict[str, Any]], List[int]]:
    """Load API configuration from a JSON file.

    Args:
        config_path: Path to the JSON config file.

    Returns:
        A tuple of (api_configs, api_concurrencies).

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the config file is invalid.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    api_configs = config_data.get("apis", [])
    if not api_configs:
        raise ValueError(f"Config file must contain a non-empty 'apis' array: {config_path}")

    # Support both formats
    api_concurrencies = config_data.get("api_concurrencies", None)
    if api_concurrencies is None:
        api_concurrencies = [api.get("concurrency", 1) for api in api_configs]

    log(f"Loaded {len(api_configs)} API configurations from {config_path}")
    log(f"API concurrencies: {api_concurrencies}")

    return api_configs, api_concurrencies


def build_api_configs_from_args(
    api_keys: List[str],
    base_urls: List[str],
    models: List[str],
) -> List[Dict[str, Any]]:
    """Build API config list from CLI arguments.

    If only one base_url or model is provided, it will be broadcast to all keys.

    Args:
        api_keys: List of API keys.
        base_urls: List of base URLs (1 or len(api_keys)).
        models: List of model names (1 or len(api_keys)).

    Returns:
        A list of API config dicts.
    """
    n = len(api_keys)

    if len(base_urls) == 1:
        base_urls = base_urls * n
    if len(models) == 1:
        models = models * n

    if len(base_urls) != n:
        raise ValueError(
            f"Number of base_urls ({len(base_urls)}) must match api_keys ({n}) or be 1"
        )
    if len(models) != n:
        raise ValueError(
            f"Number of models ({len(models)}) must match api_keys ({n}) or be 1"
        )

    configs = []
    for key, url, model in zip(api_keys, base_urls, models):
        configs.append({
            "api_key": key.strip(),
            "base_url": url.strip(),
            "model": model.strip(),
        })

    return configs


def parse_concurrencies(
    raw: Optional[str],
    api_count: int,
) -> Optional[List[int]]:
    """Parse a comma-separated concurrency string.

    Args:
        raw: Comma-separated integers, e.g. "2,2,4".
        api_count: Expected number of APIs.

    Returns:
        A list of concurrency values, or None if raw is None.
    """
    if raw is None:
        return None

    values = [int(x.strip()) for x in raw.split(",") if x.strip()]
    if not values or any(v < 1 for v in values):
        raise ValueError("Concurrency values must be positive integers")

    if len(values) == 1:
        return values * api_count
    if len(values) != api_count:
        raise ValueError(
            f"Number of concurrencies ({len(values)}) must match APIs ({api_count}) or be 1"
        )
    return values
