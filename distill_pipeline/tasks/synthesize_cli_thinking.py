"""
Synthesize Thinking task.

Takes a multi-turn conversation (messages + tools) and generates synthetic
thinking for the last non-empty assistant turn.

build_messages:
  Iterates through all messages; for each assistant role, includes its content
  (intermediate turns are kept as context). Stops before the last non-empty
  assistant message so the LLM can generate thinking for that turn.

process_result:
  Adds the generated thinking to the last assistant turn, converting its
  content from a plain string to a structured list:
    [{"type": "thinking", "thinking": <thinking>}, {"type": "text", "text": <original>}]
"""

import json
from typing import Any, Dict, List, Optional

from .base import BaseTask
from .registry import TaskRegistry
from ..utils import generate_id


@TaskRegistry.register
class SynthesizeCliThinkingTask(BaseTask):
    name = "synthesize_cli_thinking"

    def get_id(self, item: Dict[str, Any]) -> str:
        text = ""
        messages = item.get("messages", [])
        # Use the first user message content as the ID seed
        for msg in messages:
            if msg.get("role") == "user":
                return generate_id(msg.get("content", ""))
        return generate_id(json.dumps(messages, ensure_ascii=False))

    def get_id_field(self) -> Optional[str]:
        return None  # ID is computed, not a direct field

    def _find_last_assistant_idx(self, messages: List[Dict]) -> int:
        """Return index of last non-empty assistant message, or -1."""
        last_idx = -1
        for i, msg in enumerate(messages):
            if msg.get("role") == "assistant" and msg.get("content", "").strip():
                last_idx = i
        return last_idx

    def build_messages(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        messages = item.get("messages", [])
        last_idx = self._find_last_assistant_idx(messages)

        result = []
        for i, msg in enumerate(messages):
            if i >= last_idx:
                break
            role = msg.get("role", "")
            content = msg.get("content", "")
            # For assistant role: include content as-is (intermediate context)
            result.append({"role": role, "content": content})

        return result

    def process_result(
        self,
        item: Dict[str, Any],
        content: str,
        thinking: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        messages = item.get("messages", [])
        last_idx = self._find_last_assistant_idx(messages)
        if last_idx == -1:
            return None

        original_content = messages[last_idx].get("content", "")
        messages[last_idx]["content"] = [
            {"type": "thinking", "thinking": thinking or ""},
            {"type": "text", "text": original_content},
        ]
        item["messages"] = messages
        return item

    def validate_item(self, item: Dict[str, Any]) -> bool:
        messages = item.get("messages")
        if not messages:
            return False
        return self._find_last_assistant_idx(messages) != -1
