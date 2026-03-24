"""
Default OpenAI-compatible provider.

No extra_body parameters. Content only, no thinking extraction.
"""

from typing import Any, Dict, Optional, Tuple

from .base import BaseProvider


class DefaultProvider(BaseProvider):
    name = "default"

    def build_extra_body(self) -> Optional[Dict[str, Any]]:
        return None

    def extract_response(self, response: Any) -> Tuple[str, Optional[str]]:
        message = response.choices[0].message
        content = message.content or ""

        # Try to detect thinking in content via </think> tag
        if "</think>" in content and "<think>" in content:
            parts = content.split("</think>", 1)
            thinking = parts[0].split("<think>", 1)[-1]
            response_text = parts[1] if len(parts) > 1 else ""
            return response_text.strip(), thinking.strip()

        return content, None
