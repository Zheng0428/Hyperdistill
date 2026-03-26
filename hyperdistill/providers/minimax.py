"""
MiniMax provider.

MiniMax M2.5 deployed via vLLM, uses `chat_template_kwargs: {"thinking": True}`
to enable deep thinking mode.

Response parsing priority:
1. `message.reasoning_content` (vLLM reasoning parser, if enabled)
2. `<think>...</think>` tag parsing from `message.content`
"""

from typing import Any, Dict, Optional, Tuple

from .base import BaseProvider


class MiniMaxProvider(BaseProvider):
    name = "minimax"

    def build_extra_body(self) -> Optional[Dict[str, Any]]:
        return {"chat_template_kwargs": {"thinking": True}}

    def extract_response(self, response: Any) -> Tuple[str, Optional[str]]:
        message = response.choices[0].message
        content = message.content or ""

        # Priority 1: reasoning_content attribute (vLLM reasoning parser)
        reasoning_content = getattr(message, "reasoning_content", None)
        if reasoning_content is not None:
            return content, reasoning_content

        # Priority 2: parse <think>...</think> tags from content
        if "<think>" in content and "</think>" in content:
            # Extract thinking between <think> and </think>
            think_start = content.index("<think>") + len("<think>")
            think_end = content.index("</think>")
            thinking = content[think_start:think_end].strip()
            # Response is everything after </think>
            response_text = content[think_end + len("</think>"):].strip()
            return response_text, thinking

        # Fallback: </think> without <think> (truncated start)
        if "</think>" in content:
            parts = content.split("</think>", 1)
            thinking = parts[0].strip()
            response_text = parts[1].strip() if len(parts) > 1 else ""
            return response_text, thinking

        return content, None
