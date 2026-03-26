"""
GLM provider.

GLM uses `enable_thinking: False` in extra_body and returns
thinking via `message.reasoning`.
"""

from typing import Any, Dict, Optional, Tuple

from .base import BaseProvider


class GLMProvider(BaseProvider):
    name = "glm"

    def build_extra_body(self) -> Optional[Dict[str, Any]]:
        return {"enable_thinking": False}

    def extract_response(self, response: Any) -> Tuple[str, Optional[str]]:
        message = response.choices[0].message
        content = message.content or ""
        thinking = getattr(message, "reasoning", None)
        return content, thinking
