"""
Query -> Response task.

Reads `query` field from input, sends it directly as the user message,
and writes `response` and `thinking` back into the item.

Corresponds to the original gen_game_query_response.py.
"""

from typing import Any, Dict, List, Optional

from .base import BaseTask
from .registry import TaskRegistry


@TaskRegistry.register
class QueryResponseTask(BaseTask):
    name = "query_response"

    def get_id(self, item: Dict[str, Any]) -> str:
        return str(item["id"])

    def get_id_fields(self) -> Optional[List[str]]:
        """Use id field as the ID."""
        return ["id"]

    def build_messages(self, item: Dict[str, Any]) -> List[Dict[str, str]]:
        return [{"role": "user", "content": item["question"]}]

    def process_result(
        self,
        item: Dict[str, Any],
        content: str,
        thinking: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        item["response"] = content
        item["thinking"] = thinking
        return item

    def validate_item(self, item: Dict[str, Any]) -> bool:
        return "id" in item and "question" in item and bool(item.get("question"))
