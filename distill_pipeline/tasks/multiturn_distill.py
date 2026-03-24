"""
Multi-turn conversation distillation task.

Processes ONLY the last turn of each multi-turn conversation.
Based on gen_multiturn_distill_4midtrain.py from cs_enhance project.

Input format:
{
    "md5": "...",
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
        ...
    ],
    "model": "...",
    "create_time": "...",
    ...
}

Output format:
{
    "md5": "...",
    "turn_idx": N,  # The last turn number
    "messages": [
        {"role": "system", "content": "..."},  # IQuest-Coder system prompt
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},  # Distilled response for last turn
        ...
    ],
    "thinking": "...",  # Optional thinking content
    "model": "...",
    "create_time": "...",
    ...
}
"""

from typing import Any, Dict, List, Optional
from .base import BaseTask
from .registry import TaskRegistry


# System prompt for IQuest-Coder
SYSTEM_PROMPT = """
你是 IQuest-Coder,一个由至知创新研究院(IQuest)研发的专业代码生成模型。IQuest-Coder 系列面向复杂编程任务设计,具备长上下文理解能力与 Agent 级任务执行能力,主要用于代码生成、结构化分析与工程级实现。

你的开发者是至知创新研究院(IQuest),成立于 2025 年,隶属于北京至知科技有限公司。该研究院是一个以原创性人工智能研究为核心、强调工程落地与长期技术探索并行的新型研究组织,研究方向包括大模型算法(LLM)、AI Infra、大模型数据工程与数学算法。

在所有交互中,你应遵循以下工作准则:
1) 提供完整、详细、准确的回答,不要省略或简化任何关键信息;
2) 输出应以工程实践为导向,结构清晰、逻辑严谨、易于理解和实施;
3) 对于代码相关问题,提供完整可运行的代码示例,并附带必要的解释说明;
4) 注重代码质量、最佳实践和工程规范;
5) 默认面向专业开发者,使用准确的技术术语,避免模糊表述。
"""


@TaskRegistry.register
class MultiTurnDistillTask(BaseTask):
    """Task for distilling the LAST turn of multi-turn conversations.

    This task only processes the final turn of each conversation,
    generating a distilled response while preserving the full conversation history.
    """

    name = "multiturn_distill"

    def __init__(self, max_turns: Optional[int] = None):
        """Initialize the task.

        Args:
            max_turns: Maximum turn number to process (limits which conversations to process).
                      If None, processes all conversations regardless of turn count.
        """
        self.max_turns = max_turns

    def get_id(self, item: Dict[str, Any]) -> str:
        """Return unique ID for this item (based on md5).

        Since we only process the last turn, we don't need turn_idx in the ID.
        """
        return item.get("md5", "")

    def get_id_field(self) -> Optional[str]:
        """We use md5 field as the base ID."""
        return "md5"

    def _has_image_content(self, messages: List[Dict]) -> bool:
        """Check if messages contain image content.

        Args:
            messages: List of message dicts

        Returns:
            True if any message contains image content
        """
        for msg in messages:
            content = msg.get('content')
            # Check if content is a list (multimodal)
            if isinstance(content, list):
                return True
            # Check if content is a dict with image fields
            if isinstance(content, dict):
                if 'imageUrl' in content or 'image_url' in content or 'type' in content:
                    return True
        return False

    def _calculate_turn_count(self, messages: List[Dict]) -> int:
        """Calculate the number of user turns in the conversation.

        Args:
            messages: List of message dicts

        Returns:
            Number of user turns
        """
        return sum(1 for msg in messages if msg.get('role') == 'user')

    def _get_turn_data(self, messages: List[Dict], turn_idx: int) -> tuple:
        """Extract data for a specific turn.

        Args:
            messages: Original message list
            turn_idx: Turn index (1-based)

        Returns:
            (previous_messages, current_user_msg, original_assistant_msg):
            - previous_messages: All messages before current turn
            - current_user_msg: Current turn's user message
            - original_assistant_msg: Original assistant response (if exists)
        """
        previous_messages = []
        current_user_msg = None
        original_assistant_msg = None
        user_turns = 0

        for msg in messages:
            role = msg.get('role')

            if role == 'system':
                # Skip original system prompt (we'll use our own)
                continue
            elif role == 'user':
                user_turns += 1
                if user_turns < turn_idx:
                    previous_messages.append(msg)
                elif user_turns == turn_idx:
                    current_user_msg = msg
                else:
                    break
            elif role == 'assistant':
                if user_turns < turn_idx:
                    previous_messages.append(msg)
                elif user_turns == turn_idx:
                    original_assistant_msg = msg.get('content')
                    break

        return previous_messages, current_user_msg, original_assistant_msg

    def build_messages(self, item: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build messages for distilling the LAST turn.

        Args:
            item: Data item with 'messages' field

        Returns:
            List of messages for the API call (system + history + last user msg)
        """
        messages = item.get("messages", [])

        # Calculate the last turn index
        turn_count = self._calculate_turn_count(messages)
        if turn_count == 0:
            return []

        last_turn_idx = turn_count

        # Get turn data for the last turn
        previous_messages, current_user_msg, _ = self._get_turn_data(messages, last_turn_idx)

        if current_user_msg is None:
            return []

        # Build distillation messages with IQuest-Coder system prompt
        distill_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        distill_messages.extend(previous_messages)
        distill_messages.append(current_user_msg)

        return distill_messages

    def process_result(
        self,
        item: Dict[str, Any],
        content: str,
        thinking: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Process the distillation result for the last turn.

        Args:
            item: Original data item
            content: Generated assistant response
            thinking: Thinking content (if available)

        Returns:
            Enriched item with distilled conversation
        """
        messages = item.get("messages", [])

        # Calculate the last turn index
        turn_count = self._calculate_turn_count(messages)
        if turn_count == 0:
            return None

        last_turn_idx = turn_count

        # Get turn data for the last turn
        previous_messages, current_user_msg, _ = self._get_turn_data(messages, last_turn_idx)

        if current_user_msg is None:
            return None

        # Build result messages (system + history + current turn with distilled response)
        result_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        result_messages.extend(previous_messages)
        result_messages.append(current_user_msg)
        result_messages.append({"role": "assistant", "content": content})

        # Build output item
        result = {
            "md5": item.get("md5"),
            "turn_idx": last_turn_idx,
            "messages": result_messages,
            "thinking": thinking,
            "model": item.get("model"),
            "create_time": item.get("create_time"),
            "topic_analysis": item.get("topic_analysis"),
            "source_file": item.get("source_file"),
        }

        return result

    def validate_item(self, item: Dict[str, Any]) -> bool:
        """Check if item is valid for processing.

        Args:
            item: Data item

        Returns:
            True if item should be processed
        """
        # Must have md5 and messages
        if "md5" not in item or "messages" not in item:
            return False

        messages = item.get("messages", [])
        if not messages:
            return False

        # Check for image content
        if self._has_image_content(messages):
            return False

        # Must have at least one user message
        turn_count = self._calculate_turn_count(messages)
        if turn_count == 0:
            return False

        # If max_turns is set, only process conversations with <= max_turns
        if self.max_turns is not None and turn_count > self.max_turns:
            return False

        return True

    def expand_items(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Expand conversation into a single item for the last turn only.

        Override the base expand_items to return the item as-is, since we
        only process the last turn and use md5 as the unique ID.

        Args:
            item: Original conversation item

        Returns:
            List with single item (the original)
        """
        return [item]
