# synthesize_cli_content Task

## 概述

`synthesize_cli_content` 任务用于修复 CLI Agent 对话数据中内容缺失的问题。

在 CLI Agent 对话中，部分 assistant 消息的 `content` 为 `"(no content)"` 或空字符串 `""`——这类消息只有 tool calls，没有附带文字说明。本任务调用 API 为这些步骤生成简短自然语言描述（1-2 句），使对话数据完整。

## 工作原理

**展开机制**：将一条对话展开为多个 item，每个 "(no content)" assistant turn 对应一个 item，独立调用 API 合成内容。

**Prompt 设计**：
- 提供当前 turn 之前的对话上下文
- 展示该 turn 的工具调用摘要
- 展示工具调用结果（截断至 300 字符）
- 要求生成 1-2 句简短描述

**语言检测**：由于目标消息本身无文字，从前序消息中检测语言（中文/英文），自动选择对应 prompt。

**输出**：用合成内容替换原消息的 `"(no content)"` 或 `""`，返回完整对话。

## 输入格式

每条 JSONL 记录需包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `messages` | array | 对话消息列表（system/user/assistant/tool roles） |
| `tools` | array | 可用工具定义（可为空） |
| `md5` | string | 可选，如不存在将从第一条 user 消息自动生成 |

### 触发合成的 assistant 消息

```json
{
  "role": "assistant",
  "content": "(no content)",
  "tool_calls": [
    {
      "id": "call_xxx",
      "type": "function",
      "function": {
        "name": "Bash",
        "arguments": "{\"command\": \"ls -la\", \"description\": \"列出文件\"}"
      }
    }
  ]
}
```

或 `"content": ""`（空字符串）。

**注意**：无 tool_calls 的空内容消息会被跳过（无意义合成）。

## 输出格式

与输入格式相同，但目标 assistant 消息的 `content` 被替换为合成文本：

```json
{
  "role": "assistant",
  "content": "让我查看当前目录的文件结构。",
  "tool_calls": [...]
}
```

每个 "(no content)" turn 生成一条独立输出记录，包含完整的 `messages` 列表（含已修复的那条消息）。

## ID 格式

`{md5}:{msg_idx}` — md5 来自第一条 user 消息的哈希，msg_idx 为目标消息在 messages 数组中的绝对位置。

## CLI 使用

```bash
python run.py --task synthesize_cli_content \
  --backend api \
  --provider deepseek \
  --config configs/config_dpsk.json \
  -i /path/to/no_content_data.jsonl \
  -o /path/to/output.jsonl \
  -w 20
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--task synthesize_cli_content` | 使用本任务 |
| `--backend api` | 使用 API 后端（推荐） |
| `--provider` | API Provider（deepseek / kimi / default 等） |
| `--config` | Provider 配置文件路径 |
| `-i` | 输入 JSONL 文件路径 |
| `-o` | 输出 JSONL 文件路径 |
| `-w` | 并发数 |

## 生成的内容示例

| 工具调用 | 合成内容（中文） | 合成内容（英文） |
|---------|----------------|----------------|
| `Bash(command="ls -la")` | "让我查看当前目录的文件结构。" | "Let me check the current directory structure." |
| `Read(file_path="/src/main.py")` | "让我读取主文件了解代码结构。" | "Let me read the main file to understand the code structure." |
| `TodoWrite(todos=[...])` | "现在更新待办事项列表。" | "Now let me update the todo list." |

## 测试

```bash
python tests/test_synthesize_cli_content.py
```

包含 22 个单元测试，覆盖：
- 空内容检测（`"(no content)"` 和 `""`）
- 展开机制（仅展开空内容 turn）
- Prompt 构建（中英文）
- 结果处理（带/不带 `<answer>` 标签）
- 校验逻辑（各边界情况）
- Registry 注册验证
