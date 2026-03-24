"""
Shared utilities: logging, ID generation, etc.
"""

import hashlib
import time
from tqdm import tqdm


def log(message: str) -> None:
    """Print a timestamped log message (tqdm-compatible)."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    tqdm.write(f"[{timestamp}] {message}")


def generate_id(*fields: str) -> str:
    """Generate an MD5-based unique ID from one or more string fields.

    Args:
        *fields: Variable number of string fields to hash.

    Returns:
        A 32-character hex digest.
    """
    content = "|".join(fields)
    return hashlib.md5(content.encode("utf-8")).hexdigest()
