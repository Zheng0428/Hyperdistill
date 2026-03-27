# Agent-Based Q&A Generation Example

这个示例展示如何使用 Agent 和 Skill 系统生成高质量的 Q&A 数据。

## 📁 文件清单

```
examples/
├── README_AGENT_QA.md              # 本文档
├── run_qa_agent.sh                 # Agent 模式的 Q&A 生成脚本
├── run_qa_agent_example.sh         # 使用示例脚本
├── sample_qa_input.jsonl           # 示例输入数据
└── AGENT_EXAMPLE_README.md         # 详细文档
```

配套文件（在项目根目录）：
```
.claude/agents/
├── qa-expert.md                    # Q&A 专家 Agent
└── ...

.claude/skills/
├── enhanced-response-generation/
│   └── SKILL.md                    # 增强回复生成 Skill
└── ...
```

## 🚀 快速开始

### 1. 基本用法

从 examples 目录运行：

```bash
cd examples

INPUT_FILE=sample_qa_input.jsonl \
OUTPUT_FILE=output_qa_results.jsonl \
AGENTS_DIR=../.claude/agents \
SKILLS_DIR=../.claude/skills \
bash run_qa_agent.sh
```

### 2. 从项目根目录运行

```bash
INPUT_FILE=examples/sample_qa_input.jsonl \
OUTPUT_FILE=output/qa_results.jsonl \
AGENTS_DIR=./.claude/agents \
SKILLS_DIR=./.claude/skills \
bash examples/run_qa_agent.sh
```

### 3. 运行所有示例

```bash
cd examples
bash run_qa_agent_example.sh
```

## 📝 输入格式

输入文件是 JSONL 格式，每行一个问题：

```jsonl
{"id": "1", "query": "What is async/await in JavaScript?"}
{"id": "2", "query": "How does Python GIL work?"}
```

## 📊 输出格式

输出包含生成的回答和思考过程：

```jsonl
{
  "id": "1",
  "query": "What is async/await in JavaScript?",
  "response": "详细的回答内容...",
  "thinking": "分析和思考过程..."
}
```

## ⚙️ 配置参数

所有参数都可以通过环境变量设置：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `INPUT_FILE` | 必填 | 输入 JSONL 文件 |
| `OUTPUT_FILE` | 必填 | 输出 JSONL 文件 |
| `AGENT_NAME` | `qa-expert` | Agent 名称 |
| `AGENTS_DIR` | `../.claude/agents` | Agent 目录（相对于脚本位置） |
| `SKILLS` | `enhanced-response-generation` | Skill 列表（逗号分隔） |
| `SKILLS_DIR` | `../.claude/skills` | Skill 目录（相对于脚本位置） |
| `CLI_MODEL` | `sonnet` | 模型名称 |
| `WORKERS` | `4` | 并发数 |

## 💡 核心特性

### 1. QA Expert Agent

专门优化的 Q&A Agent，包含：
- 系统化的响应策略（How/Why/What 问题处理）
- 质量检查清单
- 多种问题类型支持

### 2. Enhanced Response Generation Skill

增强回复生成 Skill 提供：
- **结构化思考流程**：Phase 1 深度分析 → Phase 2 响应构建
- **质量保证机制**：清晰度、准确性、完整性、参与度
- **针对性模板**：Technical/Conceptual/Code 问题专用模板
- **自检清单**：8 项质量检查标准

### 3. 工作流程

```
Query → Agent Instructions → Skill Framework → <think> → Response
```

每个响应都包含：
1. **Thinking** (在 `<think>` 标签中)：分析、规划、质量检查
2. **Response**：结构化的高质量回答

## 📖 详细文档

查看完整文档了解更多：
```bash
cat AGENT_EXAMPLE_README.md
```

包含内容：
- 完整配置参数说明
- 工作原理详解
- 故障排查指南
- 最佳实践
- 进阶用法

## 🔧 自定义

### 使用不同的 Agent

```bash
# 查看可用 agents
ls -1 ../.claude/agents/*.md

# 使用指定 agent
AGENT_NAME=my-custom-agent bash run_qa_agent.sh
```

### 组合多个 Skills

```bash
SKILLS="enhanced-response-generation,code-analyzer,data-validator" \
bash run_qa_agent.sh
```

### 调整并发和超时

```bash
WORKERS=8 \
CLI_TIMEOUT=900 \
bash run_qa_agent.sh
```

## 📈 示例场景

### 场景 1: 技术问答数据集生成

```bash
INPUT_FILE=technical_questions.jsonl \
OUTPUT_FILE=technical_qa_dataset.jsonl \
AGENT_NAME=qa-expert \
SKILLS=enhanced-response-generation \
WORKERS=4 \
bash run_qa_agent.sh
```

### 场景 2: 代码相关问答

```bash
INPUT_FILE=code_questions.jsonl \
OUTPUT_FILE=code_qa_dataset.jsonl \
SKILLS="enhanced-response-generation,code-analyzer" \
WORKERS=4 \
bash run_qa_agent.sh
```

### 场景 3: 高质量小批量生成

```bash
INPUT_FILE=sample_qa_input.jsonl \
OUTPUT_FILE=premium_qa.jsonl \
CLI_MODEL=opus \
CLI_TIMEOUT=1200 \
WORKERS=2 \
bash run_qa_agent.sh
```

## ⚠️ 注意事项

1. **路径问题**：
   - 从 examples 目录运行时，使用 `AGENTS_DIR=../.claude/agents`
   - 从根目录运行时，使用 `AGENTS_DIR=./.claude/agents`

2. **并发控制**：
   - 建议从小并发开始测试（2-4）
   - 根据 API 限制调整

3. **断点续跑**：
   - 脚本自动检测已处理的数据
   - 中断后可以直接重新运行

## 🎯 预期效果

使用 Agent + Skill 系统后的回答质量对比：

**基础回答**:
```
Use async/await for asynchronous operations.
```

**增强回答**:
```
<think>
- 需要解释本质和优势
- 对比 Promise 方式
- 提供代码示例
- 说明常见错误
</think>

Async/await is a modern syntax for handling asynchronous operations...

**When to use it:**
- API calls, file operations, database queries...

**Benefits:**
1. Readability: eliminates callback hell
2. Error handling: use try/catch
3. Debugging: better stack traces

**Example:**
[完整代码示例]

**Common Mistakes:**
- Forgetting await
- Not handling errors
...
```

## 🚀 开始使用

1. 确保已安装依赖：
   ```bash
   pip install -r ../requirements.txt
   ```

2. 运行示例：
   ```bash
   cd examples
   bash run_qa_agent_example.sh
   ```

3. 使用自己的数据：
   ```bash
   INPUT_FILE=your_input.jsonl \
   OUTPUT_FILE=your_output.jsonl \
   AGENTS_DIR=../.claude/agents \
   SKILLS_DIR=../.claude/skills \
   bash run_qa_agent.sh
   ```

祝你生成高质量的 Q&A 数据！🎉
