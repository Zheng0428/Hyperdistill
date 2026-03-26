"""
DeepSeek provider.

DeepSeek uses `chat_template_kwargs: {"thinking": True}` for vLLM Server
and returns thinking via `message.reasoning_content` or `</think>` tag parsing.
"""

from typing import Any, Dict, Optional, Tuple

from .base import BaseProvider


class DeepSeekProvider(BaseProvider):
    name = "dpsk"

    def build_extra_body(self) -> Optional[Dict[str, Any]]:
        return {"chat_template_kwargs": {"thinking": True}}

    def extract_response(self, response: Any) -> Tuple[str, Optional[str]]:
        message = response.choices[0].message
        content = message.content or ""

        # Try reasoning_content attribute first (native DeepSeek API)
        reasoning_content = getattr(message, "reasoning_content", None)

        if reasoning_content is not None:
            return content, reasoning_content

        # Fallback: parse </think> tag from content
        if "</think>" in content and "<think>" not in content:
            parts = content.split("</think>", 1)
            thinking = parts[0]
            response_text = parts[1] if len(parts) > 1 else ""
            return response_text, thinking

        return content, None
