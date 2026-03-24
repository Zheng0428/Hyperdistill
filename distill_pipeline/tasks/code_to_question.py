"""
Code -> Question generation task.

Reads `text` field (code), wraps it in a prompt template, sends to LLM,
and extracts the question between #### markers.

Corresponds to the original gen_text.py.
"""

import re
from typing import Any, Dict, List, Optional

from .base import BaseTask
from .registry import TaskRegistry
from ..utils import generate_id


TEMPLATE_PROMPT = """You are given a code snippet. Your task is to craft a very challenging question
that can be answered ONLY by understanding the code in depth.

IMPORTANT: The generated question MUST focus on industrial/real-world application scenarios.
Consider practical use cases such as:
- Production deployment and system integration
- Performance optimization and scalability
- Error handling and edge cases in production environments
- Real-world constraints (memory, latency, concurrency, etc.)
- Integration with existing systems and APIs
- Debugging and troubleshooting in production
- Security and reliability considerations
- Business logic implementation

Rules:
- Do NOT assume any external files, types, or behaviors not shown in the code.
- Do NOT introduce new types, variants, functions, or values that are not
  explicitly present in the code.
- If the code is incomplete, ask a hard question that is still answerable
  solely from the visible code (no guessing).
- The question MUST emphasize industrial scenarios and practical applications.

You should think step-by-step and may include reasoning, but the final question MUST be wrapped between
lines that contain exactly four hash symbols (####), like:
####
<your question here>
####

The final question must be fully standalone and MUST NOT include the raw code
snippet or any direct excerpts from it.

If you mention any identifiers (e.g., function/class/variable names), define
them in the question itself so the question remains standalone.

The final question MUST be phrased as a standalone question. Do NOT refer to
any provided code snippet or say "in the provided code", "in the snippet", or
similar phrases.

Code:
{code}"""


@TaskRegistry.register
class CodeToQuestionTask(BaseTask):
    name = "code_to_question"

    def __init__(self, prompt_template: Optional[str] = None):
        self.prompt_template = prompt_template or TEMPLATE_PROMPT

    def get_id(self, item: Dict[str, Any]) -> str:
        # Generate ID from text content hash
        return item.get("data_id") or generate_id("", item.get("text", ""))

    def get_id_field(self) -> Optional[str]:
        return "data_id"

    def build_messages(self, item: Dict[str, Any]) -> List[Dict[str, str]]:
        text = item.get("text", "")
        # Clean thinking tags from text
        if text and "</think>" in text:
            text = text.split("</think>")[-1].strip()
        prompt = self.prompt_template.replace("{code}", text)
        return [{"role": "user", "content": prompt}]

    def process_result(
        self,
        item: Dict[str, Any],
        content: str,
        thinking: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        # Extract question between #### markers
        question = None
        if "####" in content:
            parts = content.split("####")
            if len(parts) >= 3:
                question = parts[1].strip()
            elif len(parts) == 2:
                question = parts[1].strip() if parts[1].strip() else parts[0].strip()

        if not question:
            return None  # Invalid result, will trigger retry

        item["prompt"] = question
        return item

    def validate_item(self, item: Dict[str, Any]) -> bool:
        text = item.get("text", "")
        if not text:
            return False
        # Clean thinking tags
        if "</think>" in text:
            text = text.split("</think>")[-1].strip()
        return bool(text)
