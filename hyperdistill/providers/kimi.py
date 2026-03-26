"""
Kimi provider.

Kimi uses `enable_thinking: False` in extra_body and returns
thinking via `message.reasoning` field.
"""

from typing import Any, Dict, Optional, Tuple

from .base import BaseProvider


class KimiProvider(BaseProvider):
    name = "kimi"

    def build_extra_body(self) -> Optional[Dict[str, Any]]:
        return {"enable_thinking": False}

    def extract_response(self, response: Any) -> Tuple[str, Optional[str]]:
        message = response.choices[0].message
        content = message.content or ""
        thinking = getattr(message, "reasoning", None)
        if not thinking:
            thinking = getattr(message, "reasoning_content", "")
        return content, thinking
