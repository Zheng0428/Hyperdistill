"""
Synthesize CLI Content task.

Expands each conversation into one item per "(no content)" assistant turn.
Each turn makes a separate API call to synthesize a brief natural-language
description of what the assistant was doing (since only tool calls were made).

Pipeline: N input conversations → M API calls (one per no-content turn) → M output records.
Output ID: md5:msg_idx

A no-content assistant message is one where content is "(no content)" or "".
These always have tool_calls but no text explanation. This task generates
1-2 sentence descriptions like "让我读取这些文件来了解代码结构。" to fill them in.

Output: replaces the "(no content)" / "" with synthesized text in-place.
"""

import copy
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from .base import BaseTask
from .registry import TaskRegistry
from ..utils import generate_id


# Values that indicate no content
_NO_CONTENT_VALUES = {"(no content)", ""}

_TOOL_CONTENT_MAX_LEN = 500   # max chars for tool result in context
_TOOL_RESULT_MAX_LEN = 300    # max chars for tool result in prompt section
_ANSWER_RE = re.compile(r"<answer>(.*?)</answer>", re.DOTALL)


# ---------------------------------------------------------------------------
# Chinese prompts
# ---------------------------------------------------------------------------

CONTENT_SYSTEM_PROMPT_ZH = """\
你是一个专业的 CLI Agent 对话内容补全器。你的任务是为 CLI 编程助手的某些步骤生成简短的文本内容描述。

## 背景

在 CLI Agent 对话中，有些 assistant 回复只包含工具调用（如读取文件、执行命令），没有附带任何文本说明。
你需要为这些步骤生成简短的自然语言描述，说明 assistant 在这一步做了什么或准备做什么。

## 风格要求

1. **语言**：中文
2. **人称**：第一人称（"让我..."、"我来..."、"现在..."）或无主语的简短描述
3. **长度**：1-2 句话（10-50 个字），模仿以下风格：
   - "让我读取这些文件来了解代码结构。"
   - "现在让我创建模型收敛性评估模块。"
   - "好的，让我创建综合示例文件。"
   - "继续添加更多功能。"
4. **内容重点**：
   - 简要说明即将执行的操作（基于工具调用）
   - 与上下文保持连贯
5. **禁止**：
   - 不要生成过长的内容
   - 不要使用 markdown 格式
   - 不要解释工具调用的技术细节
   - 不要生成与上下文无关的内容

## 输出格式

将生成的内容放在 <answer> 和 </answer> 标签中，标签外不要有任何其他内容。"""


CONTENT_SYSTEM_PROMPT_EN = """\
You are a professional CLI Agent conversation content completer. Your task is to generate brief text content for steps where the assistant only made tool calls without any text.

## Background

In CLI Agent conversations, some assistant responses only contain tool calls (like reading files, running commands) without any accompanying text description.
You need to generate brief natural language descriptions for these steps, explaining what the assistant is doing or about to do.

## Style Requirements

1. **Language**: English
2. **Perspective**: First-person ("Let me...", "I'll...", "Now...") or brief descriptions
3. **Length**: 1-2 sentences (10-50 words), mimicking styles like:
   - "Let me read these files to understand the code structure."
   - "Now let me create the model convergence evaluation module."
   - "I'll create a comprehensive example file."
   - "Continuing to add more features."
4. **Focus on**:
   - Briefly describe the operation about to be performed (based on tool calls)
   - Maintain coherence with context
5. **Do NOT**:
   - Generate overly long content
   - Use markdown formatting
   - Explain technical details of tool calls
   - Generate content unrelated to context

## Output Format

Place the generated content inside <answer> and </answer> tags. Do not include anything outside these tags."""


USER_PROMPT_TEMPLATE_ZH = """\
以下是一段 CLI Agent 对话的上下文：
<context>
{context}
</context>

在当前步骤中，assistant 执行了以下工具调用但没有附带文本说明：
<tool_calls>
{tool_calls_summary}
</tool_calls>
{tool_results_section}
请为这个步骤生成简短的文本内容（1-2 句话），描述 assistant 在做什么。
请将内容放在 <answer> 和 </answer> 标签中。"""


USER_PROMPT_TEMPLATE_EN = """\
Below is the context of a CLI Agent conversation:
<context>
{context}
</context>

At the current step, the assistant made the following tool calls without any text content:
<tool_calls>
{tool_calls_summary}
</tool_calls>
{tool_results_section}
Generate brief text content (1-2 sentences) describing what the assistant is doing.
Place the content inside <answer> and </answer> tags."""


TOOL_RESULTS_SECTION_ZH = """
以下是工具调用的结果：
<tool_results>
{tool_results}
</tool_results>
"""

TOOL_RESULTS_SECTION_EN = """
Below are the tool call results:
<tool_results>
{tool_results}
</tool_results>
"""


@TaskRegistry.register
class SynthesizeCliContentTask(BaseTask):
    name = "synthesize_cli_content"

    # ------------------------------------------------------------------
    # Helpers (shared pattern with SynthesizeCliThinkingTask)
    # ------------------------------------------------------------------

    def _base_id(self, messages: List[Dict]) -> str:
        """Stable ID seed: hash of the first user message content."""
        for msg in messages:
            if msg.get("role") == "user":
                return generate_id(msg.get("content", ""))
        return generate_id(json.dumps(messages, ensure_ascii=False))

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
                if text and text not in _NO_CONTENT_VALUES and tc_summary:
                    lines.append(f"[{lbl_ass}]: {text}\n{tc_summary}")
                elif text and text not in _NO_CONTENT_VALUES:
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

    # ------------------------------------------------------------------
    # New helpers specific to this task
    # ------------------------------------------------------------------

    def _no_content_turns(
        self, messages: List[Dict]
    ) -> Tuple[List[Tuple[int, int]], Dict[int, int]]:
        """Return [(msg_idx, nc_turn_idx), ...] for assistant messages with no content.

        A no-content message has content equal to "(no content)" or "".
        nc_turn_idx is 1-based among no-content assistant messages only.
        Also returns a reverse map: nc_turn_idx -> msg_idx.
        """
        result = []
        turn_idx_map = {}
        nc_turn = 0
        for i, msg in enumerate(messages):
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content", "")
            text = self._extract_text(content) if not isinstance(content, str) else content
            if text.strip() in _NO_CONTENT_VALUES:
                nc_turn += 1
                result.append((i, nc_turn))
                turn_idx_map[nc_turn] = i
        return result, turn_idx_map

    def _detect_lang_from_context(self, messages: List[Dict], target_msg_idx: int) -> str:
        """Detect language from surrounding context.

        The target message itself has no text, so we walk backwards through
        previous messages to find text for language detection.
        """
        for i in range(target_msg_idx - 1, -1, -1):
            msg = messages[i]
            role = msg.get("role", "")
            if role in ("user", "assistant"):
                text = self._extract_text(msg.get("content", ""))
                if text.strip() and text.strip() not in _NO_CONTENT_VALUES:
                    return self._detect_lang(text)
        # Fallback: check system message
        for msg in messages:
            if msg.get("role") == "system":
                text = self._extract_text(msg.get("content", ""))
                if text.strip():
                    return self._detect_lang(text)
        return "en"

    def _format_tool_results(
        self, messages: List[Dict], target_msg_idx: int, lang: str
    ) -> str:
        """Format tool results immediately following the target assistant message."""
        lbl_tool = "工具结果" if lang == "zh" else "Tool result"
        lbl_trunc = "...(截断)" if lang == "zh" else "...(truncated)"

        results = []
        for i in range(target_msg_idx + 1, len(messages)):
            msg = messages[i]
            if msg.get("role") != "tool":
                break
            content = self._extract_text(msg.get("content", ""))
            if content:
                truncated = content[:_TOOL_RESULT_MAX_LEN]
                if len(content) > _TOOL_RESULT_MAX_LEN:
                    truncated += lbl_trunc
                results.append(f"[{lbl_tool}]: {truncated}")
        return "\n\n".join(results)

    # ------------------------------------------------------------------
    # BaseTask interface
    # ------------------------------------------------------------------

    def get_id(self, item: Dict[str, Any]) -> str:
        md5 = item.get("md5", "")
        msg_idx = item.get("msg_idx", 0)
        return f"{md5}:{msg_idx}"

    def get_id_field(self) -> Optional[str]:
        return "md5"

    def expand_items(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Expand one conversation into one item per no-content assistant turn."""
        item["md5"] = self._base_id(item.get("messages", []))
        messages = item.get("messages")
        if not messages:
            return []

        turns, _ = self._no_content_turns(messages)
        if not turns:
            return []

        expanded = []
        for msg_idx, _nc_turn_idx in turns:
            expanded_item = copy.deepcopy(item)
            expanded_item["msg_idx"] = msg_idx
            expanded.append(expanded_item)
        return expanded

    def build_messages(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build synthesis prompt for ONE no-content assistant turn."""
        messages = item.get("messages", [])
        msg_idx = item.get("msg_idx", 0)

        if msg_idx >= len(messages):
            return []

        target_msg = messages[msg_idx]

        # Detect language from context (not the empty message itself)
        lang = self._detect_lang_from_context(messages, msg_idx)

        # Format context (all messages before this turn)
        context = self._format_context(messages, msg_idx, lang)

        # Summarize tool calls on the target message
        tool_calls_summary = self._summarize_tool_calls(
            target_msg.get("tool_calls", []), lang
        )

        # Format tool results following the target
        tool_results = self._format_tool_results(messages, msg_idx, lang)

        sys_prompt = CONTENT_SYSTEM_PROMPT_ZH if lang == "zh" else CONTENT_SYSTEM_PROMPT_EN
        usr_template = USER_PROMPT_TEMPLATE_ZH if lang == "zh" else USER_PROMPT_TEMPLATE_EN

        # Build optional tool results section
        tool_results_section = ""
        if tool_results:
            tr_template = TOOL_RESULTS_SECTION_ZH if lang == "zh" else TOOL_RESULTS_SECTION_EN
            tool_results_section = tr_template.format(tool_results=tool_results)

        user_prompt = usr_template.format(
            context=context,
            tool_calls_summary=tool_calls_summary,
            tool_results_section=tool_results_section,
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
        """Replace the no-content message with the synthesized text.

        Returns the item with messages[msg_idx]["content"] replaced,
        or None if synthesis failed (causes engine to retry/skip).
        """
        messages = item.get("messages", [])
        msg_idx = item.get("msg_idx", 0)

        if msg_idx >= len(messages):
            return None

        # Parse <answer> tag
        match = _ANSWER_RE.search(content or "")
        synth = match.group(1).strip() if match else (content or "").strip()

        if not synth:
            return None

        messages[msg_idx]["content"] = synth
        item["messages"] = messages
        return item

    def validate_item(self, item: Dict[str, Any]) -> bool:
        if "md5" not in item or "messages" not in item or "msg_idx" not in item:
            return False

        messages = item.get("messages")
        if not messages:
            return False

        msg_idx = item.get("msg_idx")
        if msg_idx is None or msg_idx >= len(messages):
            return False

        msg = messages[msg_idx]
        if msg.get("role") != "assistant":
            return False

        # Confirm it's still a no-content message (may have been pre-filled)
        content = msg.get("content", "")
        text = self._extract_text(content) if not isinstance(content, str) else content
        if text.strip() not in _NO_CONTENT_VALUES:
            return False

        # Must have tool_calls to synthesize meaningful content
        if not msg.get("tool_calls"):
            return False

        return True
