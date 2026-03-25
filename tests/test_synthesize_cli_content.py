#!/usr/bin/env python3
"""
Tests for SynthesizeCliContentTask.

Run: python tests/test_synthesize_cli_content.py
"""

import sys
import os
import copy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from distill_pipeline.tasks import TaskRegistry
from distill_pipeline.tasks.synthesize_cli_content import SynthesizeCliContentTask, _NO_CONTENT_VALUES


def make_conv(assistant_contents, include_tool_calls=True):
    """Build a minimal conversation for testing."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "请帮我分析这段代码的数据结构。"},
    ]
    for content in assistant_contents:
        msg = {"role": "assistant", "content": content}
        if content in _NO_CONTENT_VALUES and include_tool_calls:
            msg["tool_calls"] = [
                {
                    "id": "call_abc",
                    "type": "function",
                    "function": {
                        "name": "Bash",
                        "arguments": '{"command": "ls -la", "description": "列出文件"}',
                    },
                }
            ]
        messages.append(msg)
        if content in _NO_CONTENT_VALUES and include_tool_calls:
            messages.append({"role": "tool", "content": "file1.py\nfile2.py"})
    return {"messages": messages, "tools": [], "md5": "test_md5", "ass_turn_idx": 1}


def make_conv_en():
    """Build a minimal English conversation."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Please analyze this code structure."},
        {
            "role": "assistant",
            "content": "(no content)",
            "tool_calls": [
                {
                    "id": "call_en",
                    "type": "function",
                    "function": {
                        "name": "Read",
                        "arguments": '{"file_path": "/src/main.py"}',
                    },
                }
            ],
        },
        {"role": "tool", "content": "def main(): pass"},
    ]
    return {"messages": messages, "tools": [], "md5": "en_md5"}


task = SynthesizeCliContentTask()


# ------------------------------------------------------------------
# 1. _no_content_turns detection
# ------------------------------------------------------------------

def test_no_content_turns_literal():
    """Detects "(no content)" string."""
    messages = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "(no content)", "tool_calls": [{}]},
        {"role": "assistant", "content": "hello"},
        {"role": "assistant", "content": "", "tool_calls": [{}]},
    ]
    turns, turn_map = task._no_content_turns(messages)
    assert len(turns) == 2, f"Expected 2 no-content turns, got {len(turns)}"
    assert turns[0] == (1, 1)
    assert turns[1] == (3, 2)
    assert turn_map[1] == 1
    assert turn_map[2] == 3
    print("✓ _no_content_turns: detects both '(no content)' and ''")


def test_no_content_turns_none():
    """Returns empty when no no-content turns."""
    messages = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello world"},
        {"role": "assistant", "content": "more text"},
    ]
    turns, _ = task._no_content_turns(messages)
    assert len(turns) == 0
    print("✓ _no_content_turns: empty when no no-content turns")


# ------------------------------------------------------------------
# 2. expand_items
# ------------------------------------------------------------------

def test_expand_items_mixed():
    """Only expands no-content turns, not turns with content."""
    item = make_conv(["(no content)", "让我分析一下。", "(no content)"])
    expanded = task.expand_items(item)
    assert len(expanded) == 2, f"Expected 2 expanded items, got {len(expanded)}"
    # msg indices: sys=0, user=1, ass=(no content)=2, tool=3, ass=4, ass=(no content)=5, tool=6
    msg_indices = [e["msg_idx"] for e in expanded]
    assert 2 in msg_indices
    assert 5 in msg_indices
    print("✓ expand_items: only expands no-content turns")


def test_expand_items_no_empty():
    """Returns empty list when no no-content turns."""
    item = make_conv(["hello", "world"])
    expanded = task.expand_items(item)
    assert expanded == []
    print("✓ expand_items: empty list when no no-content turns")


def test_expand_items_sets_md5():
    """expand_items sets md5 from first user message."""
    item = {"messages": [
        {"role": "user", "content": "test"},
        {"role": "assistant", "content": "(no content)", "tool_calls": [{}]},
    ], "tools": []}
    expanded = task.expand_items(item)
    assert len(expanded) == 1
    assert "md5" in expanded[0]
    assert expanded[0]["md5"] != ""
    print("✓ expand_items: sets md5")


# ------------------------------------------------------------------
# 3. get_id
# ------------------------------------------------------------------

def test_get_id_format():
    """ID is md5:msg_idx."""
    item = {"md5": "abc123", "msg_idx": 4}
    assert task.get_id(item) == "abc123:4"
    print("✓ get_id: correct md5:msg_idx format")


# ------------------------------------------------------------------
# 4. build_messages — language detection
# ------------------------------------------------------------------

def test_build_messages_chinese():
    """Builds Chinese prompt for Chinese conversation."""
    item = make_conv(["(no content)"])
    item = task.expand_items(item)[0]
    msgs = task.build_messages(item)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert "中文" in msgs[0]["content"] or "CLI Agent" in msgs[0]["content"]
    assert msgs[1]["role"] == "user"
    assert "<tool_calls>" in msgs[1]["content"]
    assert "<context>" in msgs[1]["content"]
    print("✓ build_messages: Chinese prompt for Chinese conversation")


def test_build_messages_english():
    """Builds English prompt for English conversation."""
    item = make_conv_en()
    item = task.expand_items(item)[0]
    msgs = task.build_messages(item)
    assert len(msgs) == 2
    assert "English" in msgs[0]["content"] or "CLI Agent" in msgs[0]["content"]
    assert "<tool_calls>" in msgs[1]["content"]
    print("✓ build_messages: English prompt for English conversation")


def test_build_messages_includes_tool_results():
    """Tool results are included in prompt when present."""
    item = make_conv(["(no content)"])
    item = task.expand_items(item)[0]
    msgs = task.build_messages(item)
    # The conv has a tool result "file1.py\nfile2.py" after the no-content turn
    assert "tool_results" in msgs[1]["content"] or "工具" in msgs[1]["content"]
    print("✓ build_messages: tool results included")


def test_build_messages_invalid_idx():
    """Returns empty list for invalid msg_idx."""
    item = {"messages": [{"role": "user", "content": "hi"}], "msg_idx": 99, "md5": "x"}
    msgs = task.build_messages(item)
    assert msgs == []
    print("✓ build_messages: empty for invalid msg_idx")


# ------------------------------------------------------------------
# 5. process_result
# ------------------------------------------------------------------

def test_process_result_with_answer_tags():
    """Extracts content from <answer> tags and replaces no-content."""
    item = make_conv(["(no content)"])
    item = task.expand_items(item)[0]
    result = task.process_result(item, "<answer>让我查看文件结构。</answer>", None)
    assert result is not None
    msg_idx = item["msg_idx"]
    assert result["messages"][msg_idx]["content"] == "让我查看文件结构。"
    print("✓ process_result: replaces content from <answer> tags")


def test_process_result_without_tags():
    """Falls back to raw content when no <answer> tags."""
    item = make_conv(["(no content)"])
    item = task.expand_items(item)[0]
    result = task.process_result(item, "Let me check the files.", None)
    assert result is not None
    msg_idx = item["msg_idx"]
    assert result["messages"][msg_idx]["content"] == "Let me check the files."
    print("✓ process_result: falls back to raw content without tags")


def test_process_result_empty_synthesis():
    """Returns None for empty synthesis result."""
    item = make_conv(["(no content)"])
    item = task.expand_items(item)[0]
    result = task.process_result(item, "<answer>  </answer>", None)
    assert result is None
    print("✓ process_result: None for empty synthesis")


def test_process_result_invalid_idx():
    """Returns None for invalid msg_idx."""
    item = {"messages": [{"role": "user", "content": "hi"}], "msg_idx": 99, "md5": "x"}
    result = task.process_result(item, "some content", None)
    assert result is None
    print("✓ process_result: None for invalid msg_idx")


# ------------------------------------------------------------------
# 6. validate_item
# ------------------------------------------------------------------

def test_validate_item_valid():
    """Valid no-content item with tool_calls passes."""
    item = make_conv(["(no content)"])
    item = task.expand_items(item)[0]
    assert task.validate_item(item) is True
    print("✓ validate_item: valid no-content item passes")


def test_validate_item_has_content():
    """Item whose target message already has content is rejected."""
    item = make_conv(["(no content)"])
    item = task.expand_items(item)[0]
    # Manually fill in content
    item["messages"][item["msg_idx"]]["content"] = "Already has content."
    assert task.validate_item(item) is False
    print("✓ validate_item: rejects item with existing content")


def test_validate_item_no_tool_calls():
    """No-content message without tool_calls is rejected."""
    item = make_conv(["(no content)"], include_tool_calls=False)
    item["md5"] = "test"
    # Manually find and set msg_idx
    for i, m in enumerate(item["messages"]):
        if m.get("role") == "assistant" and m.get("content") == "(no content)":
            item["msg_idx"] = i
            break
    assert task.validate_item(item) is False
    print("✓ validate_item: rejects no-content without tool_calls")


def test_validate_item_missing_fields():
    """Missing required fields are rejected."""
    assert task.validate_item({}) is False
    assert task.validate_item({"md5": "x", "messages": []}) is False
    assert task.validate_item({"md5": "x", "messages": [{}], "msg_idx": 5}) is False
    print("✓ validate_item: rejects items with missing fields")


# ------------------------------------------------------------------
# 7. detect_lang_from_context
# ------------------------------------------------------------------

def test_detect_lang_from_context_zh():
    """Detects Chinese from previous user message."""
    messages = [
        {"role": "user", "content": "请帮我分析代码结构"},
        {"role": "assistant", "content": "(no content)"},
    ]
    lang = task._detect_lang_from_context(messages, 1)
    assert lang == "zh"
    print("✓ _detect_lang_from_context: detects Chinese")


def test_detect_lang_from_context_en():
    """Detects English from previous user message."""
    messages = [
        {"role": "user", "content": "Please analyze the code structure"},
        {"role": "assistant", "content": "(no content)"},
    ]
    lang = task._detect_lang_from_context(messages, 1)
    assert lang == "en"
    print("✓ _detect_lang_from_context: detects English")


def test_detect_lang_skips_no_content():
    """Skips previous no-content assistant messages when detecting lang."""
    messages = [
        {"role": "user", "content": "请帮我做这件事"},
        {"role": "assistant", "content": "(no content)"},
        {"role": "assistant", "content": "(no content)"},
    ]
    lang = task._detect_lang_from_context(messages, 2)
    assert lang == "zh"
    print("✓ _detect_lang_from_context: skips no-content assistant messages")


# ------------------------------------------------------------------
# 8. Registry registration
# ------------------------------------------------------------------

def test_registry_registration():
    """Task is registered in TaskRegistry."""
    t = TaskRegistry.get("synthesize_cli_content")
    assert isinstance(t, SynthesizeCliContentTask)
    print("✓ registry: synthesize_cli_content registered correctly")


# ------------------------------------------------------------------
# Run all tests
# ------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_no_content_turns_literal,
        test_no_content_turns_none,
        test_expand_items_mixed,
        test_expand_items_no_empty,
        test_expand_items_sets_md5,
        test_get_id_format,
        test_build_messages_chinese,
        test_build_messages_english,
        test_build_messages_includes_tool_results,
        test_build_messages_invalid_idx,
        test_process_result_with_answer_tags,
        test_process_result_without_tags,
        test_process_result_empty_synthesis,
        test_process_result_invalid_idx,
        test_validate_item_valid,
        test_validate_item_has_content,
        test_validate_item_no_tool_calls,
        test_validate_item_missing_fields,
        test_detect_lang_from_context_zh,
        test_detect_lang_from_context_en,
        test_detect_lang_skips_no_content,
        test_registry_registration,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"✗ {t.__name__}: {e}")
            failed += 1

    print(f"\n{passed}/{passed + failed} tests passed")
    if failed:
        sys.exit(1)
