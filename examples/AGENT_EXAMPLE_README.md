# Agent-Based Q&A Generation Example

这个示例展示如何使用 Agent 和 Skill 系统生成高质量的 Q&A 数据。

## 文件说明

### 1. Agent 定义
**`agents/qa_expert.md`** - Q&A 专家 Agent
- 专门用于生成高质量问答数据
- 包含完整的回答策略和质量标准
- 自动使用 `sonnet` 模型

### 2. Skill 定义
**`skills/enhanced_response_generation.md`** - 增强回复生成技能
- 提供系统化的思考和回答框架
- 包含详细的质量指南和最佳实践
- 支持多种问题类型（How/Why/What/When）

### 3. 启动脚本
**`run_qa_agent.sh`** - Agent 模式的 Q&A 生成脚本
- 基于原始 `run.sh` 改造
- 使用 CLI Backend + Agent + Skill 系统
- 支持所有配置通过环境变量覆盖

### 4. 示例数据
**`examples/sample_qa_input.jsonl`** - 示例输入数据
```jsonl
{"id": "1", "query": "What is the difference between async/await and promises in JavaScript?"}
{"id": "2", "query": "How does Python's Global Interpreter Lock (GIL) work?"}
...
```

## 快速开始

### 基本用法

```bash
# 设置输入输出文件后直接运行
INPUT_FILE=examples/sample_qa_input.jsonl \
OUTPUT_FILE=output/qa_results.jsonl \
bash run_qa_agent.sh
```

### 完整配置示例

```bash
INPUT_FILE=examples/sample_qa_input.jsonl \
OUTPUT_FILE=output/qa_results.jsonl \
AGENT_NAME=qa-expert \
SKILLS=enhanced-response-generation \
WORKERS=4 \
CLI_MODEL=sonnet \
CLI_TIMEOUT=600 \
bash run_qa_agent.sh
```

## 配置参数

### Agent/Skill 配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `AGENT_NAME` | `qa-expert` | Agent 名称 |
| `AGENTS_DIR` | `./agents` | Agent 目录 |
| `SKILLS` | `enhanced-response-generation` | Skill 列表（逗号分隔） |
| `SKILLS_DIR` | `./skills` | Skill 目录 |

### CLI 配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `CLI_CMD` | `claude` | CLI 命令 |
| `CLI_MODEL` | `sonnet` | 模型名称（会被 agent 覆盖） |
| `CLI_TIMEOUT` | `600` | 超时时间（秒） |

### 运行配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `WORKERS` | `4` | 并发数 |
| `MAX_RETRIES` | `3` | 最大重试次数 |
| `PROGRESS_THRESHOLD` | `100` | 进度阈值（%） |
| `SPLIT_MAX_LINES` | `100000` | 输出分片行数 |

### 输入输出

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `INPUT_FILE` | *必填* | 输入 JSONL 文件 |
| `OUTPUT_FILE` | *必填* | 输出 JSONL 文件 |
| `BACKEND` | `cli` | 后端类型 |
| `TASK` | `query_response` | 任务类型 |

## 输入数据格式

输入文件必须是 JSONL 格式，每行一个 JSON 对象：

```jsonl
{"id": "1", "query": "Your question here"}
{"id": "2", "query": "Another question"}
```

**必需字段**：
- `id` - 唯一标识符
- `query` - 问题内容

## 输出数据格式

输出文件格式：

```jsonl
{"id": "1", "query": "Your question here", "response": "Detailed answer...", "thinking": "Analysis process..."}
{"id": "2", "query": "Another question", "response": "Detailed answer...", "thinking": "Analysis process..."}
```

**输出字段**：
- `id` - 原始 ID
- `query` - 原始问题
- `response` - 生成的回答
- `thinking` - Agent 的思考过程（在 `<think>` 标签中）

## 工作原理

### 1. Prompt 构建顺序

当处理每个问题时，系统按以下顺序构建 prompt：

```
1. Agent Instructions (from qa_expert.md)
   ↓
2. Available Skills Section
   ├── Skill: enhanced-response-generation
   │   ├── Description
   │   ├── Tools
   │   └── Content
   ↓
3. Task Message
   └── User Query: "Your question here"
```

### 2. 响应生成流程

```
Query → Agent + Skill → Thinking (<think> tags) → Response
                        ↓
                   Quality Checks:
                   - Accuracy
                   - Completeness
                   - Clarity
                   - Examples
                   - Structure
```

### 3. 质量保证机制

Agent 使用 Skill 中定义的流程：

1. **Deep Analysis** (在 `<think>` 标签中)
   - 理解核心问题
   - 识别隐含需求
   - 确定回答策略

2. **Structured Response**
   - 直接回答
   - 详细解释
   - 实际示例
   - 最佳实践
   - 常见陷阱

3. **Self-Review**
   - 准确性检查
   - 完整性验证
   - 清晰度确认
   - 示例正确性

## 使用示例

### 示例 1: 默认配置

```bash
INPUT_FILE=examples/sample_qa_input.jsonl \
OUTPUT_FILE=output/qa_default.jsonl \
bash run_qa_agent.sh
```

### 示例 2: 高并发配置

```bash
INPUT_FILE=data/large_dataset.jsonl \
OUTPUT_FILE=output/qa_large.jsonl \
WORKERS=8 \
bash run_qa_agent.sh
```

### 示例 3: 使用不同模型

```bash
INPUT_FILE=examples/sample_qa_input.jsonl \
OUTPUT_FILE=output/qa_opus.jsonl \
CLI_MODEL=opus \
bash run_qa_agent.sh
```

### 示例 4: 组合多个 Skills

```bash
INPUT_FILE=examples/sample_qa_input.jsonl \
OUTPUT_FILE=output/qa_multi_skills.jsonl \
SKILLS="enhanced-response-generation,code-analyzer,data-validator" \
bash run_qa_agent.sh
```

### 示例 5: 自定义超时和重试

```bash
INPUT_FILE=examples/sample_qa_input.jsonl \
OUTPUT_FILE=output/qa_custom.jsonl \
CLI_TIMEOUT=900 \
MAX_RETRIES=5 \
bash run_qa_agent.sh
```

## 运行示例脚本

我们提供了完整的示例脚本：

```bash
bash examples/run_qa_agent_example.sh
```

这会运行多个示例场景，展示不同配置的使用方法。

## 断点续跑

脚本支持自动断点续跑：

1. 如果输出文件已存在，会自动检测已处理的数据
2. 只处理未完成的数据
3. 新结果追加到输出文件

**手动恢复**：
```bash
# 脚本会自动跳过已处理的 ID
INPUT_FILE=input.jsonl \
OUTPUT_FILE=output.jsonl \
bash run_qa_agent.sh
```

## 输出文件管理

### 单文件输出

默认输出到一个文件：
```
output/qa_results.jsonl
```

### 分片输出

如果输出超过 `SPLIT_MAX_LINES`（默认 100000），会自动分片：
```
output/qa_results.part0001.jsonl
output/qa_results.part0002.jsonl
output/qa_results.part0003.jsonl
```

**合并分片**：
```bash
cat output/qa_results.part*.jsonl > output/qa_results_merged.jsonl
```

## 性能调优

### 并发数建议

| 场景 | 建议 WORKERS | 说明 |
|------|--------------|------|
| 本地测试 | 2-4 | 避免过载 |
| 生产环境 | 4-8 | 根据 API 限制调整 |
| 大规模处理 | 8-16 | 确保 API 承受能力 |

### 超时时间建议

| 问题复杂度 | 建议 CLI_TIMEOUT | 说明 |
|------------|------------------|------|
| 简单问题 | 300-600s | 基本 Q&A |
| 中等复杂度 | 600-900s | 需要详细解释 |
| 复杂问题 | 900-1800s | 深度技术分析 |

## 故障排查

### 问题 1: Agent 文件不存在

```
Error: Agent file does not exist: agents/qa-expert.md
```

**解决方案**：
```bash
# 检查 agent 目录
ls -la agents/

# 或使用其他 agent
AGENT_NAME=example-agent bash run_qa_agent.sh
```

### 问题 2: Skill 文件不存在

```
Error: Skill file does not exist: skills/enhanced-response-generation.md
```

**解决方案**：
```bash
# 检查 skill 目录
ls -la skills/

# 或使用其他 skills
SKILLS="code-analyzer" bash run_qa_agent.sh
```

### 问题 3: CLI 超时

```
CLI subprocess timed out after 600s
```

**解决方案**：
```bash
# 增加超时时间
CLI_TIMEOUT=1200 bash run_qa_agent.sh
```

### 问题 4: 并发过高导致失败

**解决方案**：
```bash
# 降低并发数
WORKERS=2 bash run_qa_agent.sh
```

## 自定义 Agent 和 Skill

### 创建自定义 Agent

1. 在 `agents/` 目录创建新文件：
```bash
vim agents/my_custom_agent.md
```

2. 添加 YAML frontmatter 和内容：
```markdown
---
name: my-custom-agent
model: sonnet
description: My custom Q&A agent
---

# My Custom Agent Instructions
...
```

3. 使用自定义 agent：
```bash
AGENT_NAME=my-custom-agent bash run_qa_agent.sh
```

### 创建自定义 Skill

1. 在 `skills/` 目录创建新文件：
```bash
vim skills/my_custom_skill.md
```

2. 添加内容：
```markdown
---
name: my-custom-skill
description: My custom skill
tools: [Read, Write]
---

# My Custom Skill Instructions
...
```

3. 使用自定义 skill：
```bash
SKILLS="enhanced-response-generation,my-custom-skill" bash run_qa_agent.sh
```

## 与原始 run.sh 的对比

| 特性 | run.sh (API) | run_qa_agent.sh (Agent) |
|------|--------------|-------------------------|
| 后端类型 | API | CLI |
| Provider | 需要配置 | 不需要 |
| 健康检查 | 需要 | 不需要 |
| Agent 系统 | 不支持 | 支持 |
| Skill 系统 | 不支持 | 支持 |
| 模型配置 | 固定 | 可由 Agent 覆盖 |
| Thinking | 可能有 | 始终包含 |
| 响应质量 | 依赖 prompt | Agent + Skill 增强 |

## 最佳实践

1. **从小数据集开始测试**
   ```bash
   # 先用 5-10 条数据测试
   head -10 large_input.jsonl > test_input.jsonl
   INPUT_FILE=test_input.jsonl OUTPUT_FILE=test_output.jsonl bash run_qa_agent.sh
   ```

2. **逐步增加并发数**
   ```bash
   # 从低并发开始
   WORKERS=2 bash run_qa_agent.sh
   # 确认稳定后再增加
   WORKERS=4 bash run_qa_agent.sh
   ```

3. **监控输出质量**
   ```bash
   # 随机抽样检查
   shuf -n 5 output.jsonl | jq .
   ```

4. **定期备份输出**
   ```bash
   # 定期复制输出文件
   cp output.jsonl backup/output_$(date +%Y%m%d_%H%M%S).jsonl
   ```

## 进阶用法

### 使用环境变量配置 API

```bash
# 使用自定义 API 端点
export ANTHROPIC_BASE_URL="https://your-endpoint.com"
export ANTHROPIC_API_KEY="sk-your-key"

INPUT_FILE=input.jsonl OUTPUT_FILE=output.jsonl bash run_qa_agent.sh
```

### 批处理多个文件

```bash
#!/bin/bash
for input_file in data/*.jsonl; do
    filename=$(basename "$input_file" .jsonl)
    INPUT_FILE="$input_file" \
    OUTPUT_FILE="output/${filename}_processed.jsonl" \
    bash run_qa_agent.sh
done
```

### 并行处理（谨慎使用）

```bash
# 将大文件分割后并行处理
split -l 1000 large_input.jsonl split_
for file in split_*; do
    INPUT_FILE="$file" \
    OUTPUT_FILE="output/${file}.jsonl" \
    bash run_qa_agent.sh &
done
wait
```

## 总结

这个 Agent 模式的 Q&A 生成系统提供了：

✅ **高质量输出** - 通过 Agent 和 Skill 系统确保响应质量
✅ **灵活配置** - 所有参数可通过环境变量覆盖
✅ **自动断点续跑** - 支持中断后恢复
✅ **易于扩展** - 可自定义 Agent 和 Skill
✅ **生产就绪** - 包含完整的错误处理和日志

开始使用：
```bash
INPUT_FILE=examples/sample_qa_input.jsonl \
OUTPUT_FILE=output/qa_results.jsonl \
bash run_qa_agent.sh
```
