"""
Synthesize CLI Thinking task.

Expands each conversation into one item per non-empty assistant turn.
Each turn makes a separate API call with context up to that turn.
Each turn writes one output record (like multiturn_all_distill).

Pipeline: 5 input conversations → N API calls (one per turn) → N output records.
Output ID: md5:ass_turn_idx

Output format per assistant message:
  - reasoning_content: synthesized thinking text
  - content: original content (list content joined with \\n)
"""

import copy
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from .base import BaseTask
from .registry import TaskRegistry
from ..utils import generate_id


# ---------------------------------------------------------------------------
# Chinese prompts (per-turn)
# ---------------------------------------------------------------------------

SYNTH_SYSTEM_PROMPT_ZH = """\
你是一个专业的 thinking 内容合成器。你的任务是为一个 CLI 编程助手的每一步回复生成简洁的内部思考过程。

## 风格要求

1. **语言**：中文
2. **人称**：第一人称内心独白（"让我..."、"我需要..."、"我应该..."）
3. **长度**：
   - 简单操作（调用单个工具、简短回复）：1-2 句话
   - 中等复杂度（分析结果、规划下一步）：2-4 句话
   - 复杂分析/规划（首次理解需求、多步骤规划、总结）：4-8 句话
4. **内容重点**：
   - 理解当前状况（用户要什么、工具返回了什么）
   - 推理和判断（为什么选择这个方案/工具）
   - 下一步行动（接下来要做什么）
5. **禁止**：
   - 不要重复 assistant 回复的原文
   - 不要生成与上下文无关的内容
   - 不要使用 markdown 格式（如标题、列表符号）

## 输出格式

将思考内容放在 <answer> 和 </answer> 标签中，标签外不要有任何其他内容。"""


SYNTH_SYSTEM_PROMPT_EN = """\
You are a professional thinking content synthesizer. Your task is to generate concise internal thinking traces for each step of a CLI coding assistant's response.

## Style Requirements

1. **Language**: English
2. **Perspective**: First-person internal monologue ("Let me...", "I need to...", "I should...")
3. **Length**:
   - Simple actions (single tool call, brief reply): 1-2 sentences
   - Medium complexity (analyzing results, planning next step): 2-4 sentences
   - Complex analysis/planning (understanding requirements, multi-step planning, summarizing): 4-8 sentences
4. **Focus on**:
   - Understanding the current situation (what the user wants, what the tool returned)
   - Reasoning and judgment (why this approach/tool was chosen)
   - Next action (what to do next)
5. **Do NOT**:
   - Repeat the assistant's response verbatim
   - Generate content unrelated to the context
   - Use markdown formatting (headings, bullet points)

## Output Format

Place the thinking content inside <answer> and </answer> tags. Do not include anything outside these tags."""


USER_PROMPT_TEMPLATE_ZH = """\
以下是一段 CLI Agent 对话的上下文：
<context>
{context}
</context>

以下是 assistant 在当前步骤的回复：
<response>
{target_response}
</response>

请为这段 assistant 回复生成简洁的内部思考过程（thinking）。
请将思考内容放在 <answer> 和 </answer> 标签中。"""


USER_PROMPT_TEMPLATE_EN = """\
Below is the context of a CLI Agent conversation:
<context>
{context}
</context>

Below is the assistant's response at the current step:
<response>
{target_response}
</response>

Generate a concise internal thinking trace for this assistant response.
Place the thinking content inside <answer> and </answer> tags."""


_TOOL_CONTENT_MAX_LEN = 500
_ANSWER_RE = re.compile(r"<answer>(.*?)</answer>", re.DOTALL)


@TaskRegistry.register
class SynthesizeCliThinkingTask(BaseTask):
    name = "synthesize_cli_thinking"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _base_id(self, messages: List[Dict]) -> str:
        """Stable ID seed: hash of the first user message content."""
        content = ""
        for msg in messages:
            content = content + "\n" +msg.get("content", "")
        return generate_id(content)

    def _assistant_turns(self, messages: List[Dict]) -> List[Tuple[int, int]]:
        """Return [(msg_idx, ass_turn_idx), ...] for all non-empty assistant messages.

        ass_turn_idx is 1-based among non-empty assistant messages only.
        """
        turn_idx_map = {}
        result = []
        ass_turn = 0
        for i, msg in enumerate(messages):
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content", "")
            text = self._extract_text(content) if not isinstance(content, str) else content
            if text.strip():
                ass_turn += 1
                result.append((i, ass_turn))
                turn_idx_map[ass_turn] = i
        return result, turn_idx_map

    @staticmethod
    def _extract_text(content) -> str:
        """Extract plain text from content (string or list of content blocks)."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text", "")
                    if text:
                        parts.append(text)
                elif isinstance(block, str):
                    parts.append(block)
            return "\n".join(parts)
        return str(content) if content else ""

    @staticmethod
    def _detect_lang(text: str) -> str:
        """Detect whether text is primarily Chinese or English."""
        if not text:
            return "en"
        cjk_count = sum(
            1 for ch in text
            if '\u4e00' <= ch <= '\u9fff'
            or '\u3400' <= ch <= '\u4dbf'
            or '\uf900' <= ch <= '\ufaff'
        )
        alpha_count = sum(1 for ch in text if ch.isalpha())
        if alpha_count == 0:
            return "zh" if cjk_count > 0 else "en"
        return "zh" if cjk_count / alpha_count > 0.1 else "en"

    @staticmethod
    def _summarize_tool_calls(tool_calls: List[Dict], lang: str = "zh") -> str:
        """Summarize tool_calls as brief text."""
        if not tool_calls:
            return ""
        parts = []
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name", "unknown")
            args_str = fn.get("arguments", "")
            brief = ""
            if args_str:
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                    if isinstance(args, dict):
                        for k, v in args.items():
                            v_str = str(v)
                            if len(v_str) > 60:
                                v_str = v_str[:57] + "..."
                            brief = f'{k}="{v_str}"'
                            break
                except (json.JSONDecodeError, TypeError):
                    pass
            parts.append(f"{name}({brief})" if brief else name)
        label = "调用工具" if lang == "zh" else "Tool calls"
        return f"[{label}: {', '.join(parts)}]"

    def _format_context(self, messages: List[Dict], target_msg_idx: int, lang: str = "zh") -> str:
        """Format all messages before the target turn as structured context."""
        lbl_user = "用户" if lang == "zh" else "User"
        lbl_ass = "助手" if lang == "zh" else "Assistant"
        lbl_tool = "工具结果" if lang == "zh" else "Tool result"
        lbl_trunc = "...(截断)" if lang == "zh" else "...(truncated)"

        lines = []
        for msg in messages[:target_msg_idx]:
            role = msg.get("role", "")
            content = self._extract_text(msg.get("content", ""))

            if role == "system":
                continue
            elif role == "user":
                lines.append(f"[{lbl_user}]: {content}")
            elif role == "assistant":
                text = content.strip()
                tc_summary = self._summarize_tool_calls(msg.get("tool_calls", []), lang)
                if text and tc_summary:
                    lines.append(f"[{lbl_ass}]: {text}\n{tc_summary}")
                elif text:
                    lines.append(f"[{lbl_ass}]: {text}")
                elif tc_summary:
                    lines.append(f"[{lbl_ass}]: {tc_summary}")
            elif role == "tool":
                if content:
                    truncated = content[:_TOOL_CONTENT_MAX_LEN]
                    if len(content) > _TOOL_CONTENT_MAX_LEN:
                        truncated += lbl_trunc
                    lines.append(f"[{lbl_tool}]: {truncated}")

        return "\n\n".join(lines)

    def _format_target_response(self, msg: Dict, lang: str = "zh") -> str:
        """Format the target assistant message (content + tool_calls)."""
        content = self._extract_text(msg.get("content", ""))
        tc_summary = self._summarize_tool_calls(msg.get("tool_calls", []), lang)

        parts = []
        if content.strip():
            parts.append(content.strip())
        if tc_summary:
            parts.append(tc_summary)
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # BaseTask interface
    # ------------------------------------------------------------------

    def get_id(self, item: Dict[str, Any]) -> str:
        md5 = item.get("md5", "")
        msg_turn_idx = item.get("msg_turn_idx", 1)
        return f"{md5}:{msg_turn_idx}"

    def get_id_fields(self) -> Optional[List[str]]:
        """Compose ID from md5 and msg_turn_idx."""
        return ["md5", "msg_turn_idx"]

    def expand_items(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Expand one conversation into one item per non-empty assistant turn."""
        item["md5"] = self._base_id(item.get("messages", []))
        messages = item.get("messages")
        if not messages:
            return []

        expanded = []
        for _msg_idx, msg in enumerate(messages):
            if msg.get("role") != "assistant":
                continue
            expanded_item = copy.deepcopy(item)
            expanded_item["msg_turn_idx"] = _msg_idx

            if msg.get("reasoning_content") is None:
                expanded.append(expanded_item)
        return expanded

    def build_messages(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build synthesis prompt for ONE assistant turn.

        Uses all messages before the target turn as context, plus the
        target assistant response. Detects language to pick prompt.
        """
        messages = item.get("messages", [])
        msg_turn_idx = item.get("msg_turn_idx", None)
        if msg_turn_idx is None:
            return []

        # Detect language from the target assistant content
        target_content = self._extract_text(messages[msg_turn_idx].get("content", ""))
        lang = self._detect_lang(target_content)

        context = self._format_context(messages, msg_turn_idx, lang)
        target_response = self._format_target_response(messages[msg_turn_idx], lang)

        sys_prompt = SYNTH_SYSTEM_PROMPT_ZH if lang == "zh" else SYNTH_SYSTEM_PROMPT_EN
        usr_template = USER_PROMPT_TEMPLATE_ZH if lang == "zh" else USER_PROMPT_TEMPLATE_EN

        user_prompt = usr_template.format(
            context=context,
            target_response=target_response,
        )

        return [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def process_result(
        self,
        item: Dict[str, Any],
        content: str,
        thinking: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Process one turn's API result. Returns a per-turn record.

        Each expanded item produces one output record with the target
        assistant message's reasoning_content and normalized content.
        """
        messages = item.get("messages", [])
        msg_turn_idx = item.get("msg_turn_idx", None)
        if msg_turn_idx is None:
            return None

        # Parse <answer> tag
        match = _ANSWER_RE.search(content or "")
        synth = match.group(1).strip() if match else (content or "").strip()

        msg = messages[msg_turn_idx]

        # Normalize content: list → join with \n
        original_content = msg.get("content", "")
        if isinstance(original_content, list):
            original_content = self._extract_text(original_content)

        # Add reasoning_content to the target message
        # msg["content"] = original_content
        msg["reasoning_content"] = synth

        item["messages"] = messages
        return item

    def validate_item(self, item: Dict[str, Any]) -> bool:
        if "md5" not in item or "messages" not in item or "msg_turn_idx" not in item:
            return False
        
        messages = item.get("messages")
        if not messages:
            return False

        # check for reasoning_content 
        msg_turn_idx = item.get("msg_turn_idx")
        if msg_turn_idx is None:
            return False

        # turn_message = messages[turn_idx]
        # if turn_message.get("reasoning_content") is None:
        #     return False
        return True
