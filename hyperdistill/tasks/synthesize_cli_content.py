"""
Synthesize CLI Content task.

Expands each conversation into one item per "(no content)" assistant turn.
Each turn makes a separate API call to synthesize a brief natural-language
description of what the assistant was doing (since only tool calls were made).

Pipeline: N input conversations → M API calls (one per no-content turn) → M output records.
Output ID: md5:msg_turn_idx

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


# Values that indicate no content (exact match after strip; see _plain_text_is_no_content)
_NO_CONTENT_VALUES = {"(no content)", ""}


def _plain_text_is_no_content(text: str) -> bool:
    """True if visible assistant text is empty or the usual '(no content)' placeholder."""
    if not isinstance(text, str):
        return False
    s = text.strip()
    if not s:
        return True
    if s.lower() == "(no content)":
        return True
    if "(no content)" in s.lower()[:20]:
        return True
    return False

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

## 风格要求（对齐真实 CLI 外显回复）

参考同类对话里常见的说法，语气应自然、协作，像在对用户说话。

1. **语言**：中文
2. **开头习惯**（任选自然的一种，勿堆砌）：
   - 行动：「让我…」「现在让我…」「首先让我了解一下…」
   - 协作：「我来帮你…」「好的，我来…」
   - 情境观察 + 行动：「当前目录是空的，我来为你创建…」「脚本运行成功！现在验证…」「发现问题了！需要修复…」
3. **长度**：通常 1–2 句、约 10–60 字；若需先说明情境再写动作，可用两句，但不要写成长篇说明。
4. **内容重点**：
   - 基于工具调用与上文，说清楚这一步要做什么或为什么要先看什么
   - 可以先报告工具结果（一句），再说下一步动作（一句）
   - 与上下文连贯，像紧接在前后文之后的下一句回复
5. **禁止**：
   - 不要输出 <think>…</think> 思考块或内部独白，只写对用户可见的内容
   - 不要用多级标题、大段列表等复杂 Markdown；plain 文本即可
   - 不要复述工具 JSON/XML 细节；不要跑题

## 典型风格示例

- "我来帮你编写批量删除 StatefulSet 的脚本。首先让我了解一下当前的项目结构。"
- "当前目录是空的，我来为你创建项目结构。"
- "Go 未安装在当前环境中。让我为你完善这个脚本，添加更多有用的功能。"
- "让我更新 go.mod 文件使用兼容的版本。"
- "脚本运行成功！现在验证生成的文件。"
- "现在运行测试验证实现是否正确。"
- "发现问题了！需要修复原始代码确保对角线为 0。"
- "需要先安装依赖。"

## 输出格式

将生成的内容放在 <answer> 和 </answer> 标签中，标签外不要有任何其他内容。"""


CONTENT_SYSTEM_PROMPT_EN = """\
You are a professional CLI Agent conversation content completer. Your task is to generate brief text content for steps where the assistant only made tool calls without any text.

## Background

In CLI Agent conversations, some assistant responses only contain tool calls (like reading files, running commands) without any accompanying text description.
You need to generate brief natural language descriptions for these steps, explaining what the assistant is doing or about to do.

## Style Requirements (match typical CLI assistant replies)

Tone should sound helpful and conversational, like the visible reply a user would see before/after tool use.

1. **Language**: English
2. **Openings that fit well** (pick one natural phrasing; do not stack them):
   - Action: "Let me...", "Now let me...", "Let me first check..."
   - Collaborative: "I'll help you...", "I'll..."
   - Situation-first: "The directory is empty. I'll...", "I see two issues. Let me fix both."
   - Status + next action: "Both versions work correctly. Let me verify...", "The test is failing. Let me fix..."
3. **Length**: Usually 1–2 short sentences (~10–50 words). Two sentences are fine when a quick situational lead-in helps.
4. **Focus on**:
   - What this step is doing or why you are inspecting something first (aligned with tool calls and prior context)
   - Can report a brief observation first, then state the next action
   - Stay contiguous with the conversation; sound like the next assistant line
5. **Do NOT**:
   - Emit <think>...</think> blocks or internal monologue; user-facing text only
   - Use heavy markdown (headings, long lists); plain sentences are enough
   - Dump raw tool-call payloads or unrelated content

## Typical Style Examples

- "Let me first check the current directory structure to understand the project state."
- "The directory is empty. I'll create the implementation from scratch."
- "Now let me test the implementation with a simple example."
- "Now let me compile and test the C++ program."
- "Both versions work correctly. Let me verify they produce the same output."
- "I see two issues: the script needs to run with python3 and the expected values need correction. Let me fix both."
- "The issue is the error message is printed to stdout, not stderr. Let me fix the test."

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
请为这个步骤生成简短的外显回复（1–3 句），风格与同任务里常见的 assistant 可见内容一致：协作口吻、可先说明情境再写将执行的操作。
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
Generate brief user-visible text (1–3 short sentences) in the same tone as typical CLI assistant replies: collaborative, may lead with context then state the next action.
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
        """Stable ID seed: hash of user/tool content and assistant reasoning_content."""
        parts = []
        for msg in messages:
            role = msg.get("role", "")
            if role in ("user", "tool"):
                parts.append(str(msg.get("content", "") or ""))
            elif role == "assistant":
                parts.append(str(msg.get("reasoning_content", "") or ""))
        return generate_id("\n".join(parts))

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
        return "zh" if cjk_count / alpha_count > 0.01 else "en"

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
                if text and not _plain_text_is_no_content(content) and tc_summary:
                    lines.append(f"[{lbl_ass}]: {text}\n{tc_summary}")
                elif text and not _plain_text_is_no_content(content):
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
            if _plain_text_is_no_content(text):
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
            if msg.get("role") == "user":
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
        msg_turn_idx = item.get("msg_turn_idx", 0)
        return f"{md5}:{msg_turn_idx}"

    def get_id_fields(self) -> Optional[List[str]]:
        """Compose ID from md5 and msg_turn_idx."""
        return ["md5", "msg_turn_idx"]

    def expand_items(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Expand one conversation into one item per assistant turn that needs content synthesis.

        Includes turns where content is missing ("(no content)" / "") and turns
        where existing content language does not match the user content language.
        """
        item["md5"] = self._base_id(item.get("messages", []))
        messages = item.get("messages")
        if not messages:
            return []

        expanded = []
        for i, msg in enumerate(messages):
            if msg.get("role") != "assistant":
                continue
            
            content = msg.get("content", "")
            text = self._extract_text(content) if not isinstance(content, str) else content
            if _plain_text_is_no_content(text):
                # No content — needs synthesis
                expanded_item = copy.deepcopy(item)
                expanded_item["msg_turn_idx"] = i
                expanded.append(expanded_item)
            else:
                # Has content — re-synthesize if language mismatches user content
                expected_lang = self._detect_lang_from_context(messages, i)
                actual_lang = self._detect_lang(text)
                if actual_lang != expected_lang:
                    expanded_item = copy.deepcopy(item)
                    expanded_item["msg_turn_idx"] = i
                    expanded.append(expanded_item)
        return expanded

    def build_messages(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build synthesis prompt for ONE no-content assistant turn."""
        messages = item.get("messages", [])
        msg_turn_idx = item.get("msg_turn_idx", 0)

        if msg_turn_idx >= len(messages):
            return []

        target_msg = messages[msg_turn_idx]

        # Detect language from context (not the empty message itself)
        lang = self._detect_lang_from_context(messages, msg_turn_idx)

        # Format context (all messages before this turn)
        context = self._format_context(messages, msg_turn_idx, lang)

        # Summarize tool calls on the target message
        tool_calls_summary = self._summarize_tool_calls(
            target_msg.get("tool_calls", []), lang
        )

        # Format tool results following the target
        tool_results = self._format_tool_results(messages, msg_turn_idx, lang)

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

        Returns the item with messages[msg_turn_idx]["content"] replaced,
        or None if synthesis failed (causes engine to retry/skip).
        """
        messages = item.get("messages", [])
        msg_turn_idx = item.get("msg_turn_idx", 0)

        if msg_turn_idx >= len(messages):
            return None

        # Parse <answer> tag
        match = _ANSWER_RE.search(content or "")
        synth = match.group(1).strip() if match else (content or "").strip()

        if not synth:
            return None

        messages[msg_turn_idx]["content"] = synth
        item["messages"] = messages
        return item

    def validate_item(self, item: Dict[str, Any]) -> bool:
        if "md5" not in item or "messages" not in item or "msg_turn_idx" not in item:
            return False

        messages = item.get("messages")
        if not messages:
            return False

        msg_turn_idx = item.get("msg_turn_idx")
        if msg_turn_idx is None or msg_turn_idx >= len(messages):
            return False

        msg = messages[msg_turn_idx]
        if msg.get("role") != "assistant":
            return False

        return True
