"""
Synthesize CLI Thinking task.

Expands each conversation into one item per non-empty assistant turn.
For each turn, synthesizes a thinking trace and writes it back into that
assistant message as a structured content block:
  [{"type": "thinking", "thinking": <thinking>}, {"type": "text", "text": <original>}]

expand_items:
  One input conversation → N items (one per non-empty assistant turn).
  Each item carries the original messages + ass_turn_idx (1-based).

get_id:
  "<first_user_msg_hash>:<ass_turn_idx>"

build_messages:
  TODO: to be specified. Placeholder sends all messages before the target turn.

process_result:
  Finds the ass_turn_idx-th non-empty assistant message and attaches thinking.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from .base import BaseTask
from .registry import TaskRegistry
from ..utils import generate_id


@TaskRegistry.register
class SynthesizeCliThinkingTask(BaseTask):
    name = "synthesize_cli_thinking"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _base_id(self, messages: List[Dict]) -> str:
        """Stable ID seed: hash of the first user message content."""
        for msg in messages:
            if msg.get("role") == "user":
                return generate_id(msg.get("content", ""))
        return generate_id(json.dumps(messages, ensure_ascii=False))

    def _assistant_turns(self, messages: List[Dict]) -> List[Tuple[int, int]]:
        """Return [(msg_idx, ass_turn_idx), ...] for all non-empty assistant messages.

        ass_turn_idx is 1-based among non-empty assistant messages only.
        """
        result = []
        ass_turn = 0
        for i, msg in enumerate(messages):
            if msg.get("role") == "assistant" and msg.get("content", "").strip():
                ass_turn += 1
                result.append((i, ass_turn))
        return result

    # ------------------------------------------------------------------
    # BaseTask interface
    # ------------------------------------------------------------------

    def get_id(self, item: Dict[str, Any]) -> str:
        messages = item.get("messages", [])
        ass_turn_idx = item.get("ass_turn_idx", 1)
        return f"{self._base_id(messages)}:{ass_turn_idx}"

    def get_id_field(self) -> Optional[str]:
        return None  # computed

    def expand_items(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Expand one conversation into one item per non-empty assistant turn."""
        messages = item.get("messages")
        if not messages:
            return []

        turns = self._assistant_turns(messages)
        if not turns:
            return []

        expanded = []
        for _msg_idx, ass_turn_idx in turns:
            expanded_item = dict(item)
            expanded_item["ass_turn_idx"] = ass_turn_idx
            expanded.append(expanded_item)
        return expanded

    def build_messages(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """TODO: build the messages to send to the LLM for thinking synthesis.

        Currently sends all messages before the target assistant turn as context.
        """
        messages = item.get("messages", [])
        ass_turn_idx = item.get("ass_turn_idx", 1)

        turns = self._assistant_turns(messages)
        # Find the message index of the target turn
        target_msg_idx = next(
            (msg_idx for msg_idx, t in turns if t == ass_turn_idx), -1
        )
        if target_msg_idx == -1:
            return []

        return [
            {"role": msg.get("role", ""), "content": msg.get("content", "")}
            for msg in messages[:target_msg_idx]
        ]

    def process_result(
        self,
        item: Dict[str, Any],
        content: str,
        thinking: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        messages = item.get("messages", [])
        ass_turn_idx = item.get("ass_turn_idx", 1)

        turns = self._assistant_turns(messages)
        target_msg_idx = next(
            (msg_idx for msg_idx, t in turns if t == ass_turn_idx), -1
        )
        if target_msg_idx == -1:
            return None

        original_content = messages[target_msg_idx].get("content", "")
        messages[target_msg_idx]["content"] = [
            {"type": "thinking", "thinking": thinking or ""},
            {"type": "text", "text": original_content},
        ]
        item["messages"] = messages
        return item

    def validate_item(self, item: Dict[str, Any]) -> bool:
        messages = item.get("messages")
        if not messages:
            return False
        ass_turn_idx = item.get("ass_turn_idx")
        if ass_turn_idx is None:
            return False
        turns = self._assistant_turns(messages)
        return any(t == ass_turn_idx for _, t in turns)
