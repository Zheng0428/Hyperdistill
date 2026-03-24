"""
Text + Prompt -> Response task.

Reads `prompt` and `text` fields, concatenates them as the user message,
and writes `response` back into the item.

Corresponds to the original gen_response.py.
"""

from typing import Any, Dict, List, Optional

from .base import BaseTask
from .registry import TaskRegistry
from ..utils import generate_id


@TaskRegistry.register
class TextToResponseTask(BaseTask):
    name = "text_to_response"

    def get_id(self, item: Dict[str, Any]) -> str:
        return item.get("data_id") or generate_id("", item.get("text", ""))

    def get_id_field(self) -> Optional[str]:
        return "data_id"

    def build_messages(self, item: Dict[str, Any]) -> List[Dict[str, str]]:
        prompt = item.get("prompt", "")
        text = item.get("text", "")
        content = f"{prompt}\n{text}" if prompt else text
        return [{"role": "user", "content": content}]

    def process_result(
        self,
        item: Dict[str, Any],
        content: str,
        thinking: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        # Handle thinking tag in content
        if "</think>" in content and "<think>" not in content:
            content = "<think>" + content

        item["response"] = content
        if thinking is not None:
            item["thinking"] = thinking
        return item

    def validate_item(self, item: Dict[str, Any]) -> bool:
        return bool(item.get("text")) and bool(item.get("prompt"))
