# Distill Pipeline

LLM 数据蒸馏框架 —— 模块化、可扩展、开箱即用。

支持两种执行后端：
- **API Backend**：通过 OpenAI 兼容 API 批量调用 LLM（AsyncOpenAI）
- **CLI Backend**：通过 subprocess 调用 CLI Agent（如 `claude --bare`）

两种后端共享同一套 DataLoader、Task、OutputWriter、断点续跑/去重基础设施。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. API Backend 模式（默认）

通过 OpenAI 兼容 API 调用 LLM：

```bash
# 配置 API（编辑 configs/ 下的 JSON 文件）
python run.py \
  --task query_response \
  --provider minimax \
  --config configs/config_minimax.json \
  -i /path/to/input.jsonl \
  -o /path/to/output.jsonl \
  --temperature 1.0 --top_p 0.95
```

### 3. CLI Backend 模式（Agent 蒸馏）

通过 subprocess 调用 `claude` CLI 或其他 Agent：

```bash
# 基本用法
python run.py \
  --task stackoverflow \
  --backend cli \
  --cli-model sonnet \
  --agent-instructions /path/to/agent.md \
  -i /path/to/input.jsonl \
  -o /path/to/output.jsonl \
  -w 4

# 使用自定义 API 端点
ANTHROPIC_BASE_URL="https://your-endpoint.com" \
ANTHROPIC_API_KEY="sk-xxx" \
python run.py \
  --task stackoverflow \
  --backend cli \
  --cli-model MiniMax-M2.5 \
  --agent-instructions agent.md \
  -i input.jsonl -o output.jsonl
```

### 4. 通用 Shell 脚本

```bash
TASK=query_response \
PROVIDER=glm \
CONFIG_FILE=configs/config_glm.json \
INPUT_FILE=/data/input.jsonl \
OUTPUT_FILE=/data/output.jsonl \
bash run.sh
```

## 项目结构

```
distill_pipeline/
├── distill_pipeline/              # 核心包
│   ├── config.py                  # API 配置加载
│   ├── utils.py                   # 日志、ID 生成
│   ├── engine.py                  # 核心异步引擎（Backend 无关）
│   ├── output_writer.py           # 分片输出 + 去重 + 断点续跑（流式扫描）
│   ├── client_pool.py             # 异步客户端池（并发展开、随机负载、热重载）
│   ├── health_check.py            # API 健康检查
│   ├── filters.py                 # 后处理过滤器
│   ├── backends/                  # 执行后端
│   │   ├── base.py                #   BaseBackend ABC
│   │   ├── api_backend.py         #   API 后端（AsyncOpenAI）
│   │   └── cli_backend.py         #   CLI 后端（subprocess agent）
│   ├── dataloader/                # 数据加载（流式）
│   │   ├── base.py                #   BaseDataLoader ABC
│   │   ├── jsonl_loader.py        #   JSONL 流式加载器
│   │   ├── parquet_loader.py      #   Parquet 批流式加载器
│   │   └── registry.py            #   按扩展名自动匹配
│   ├── providers/                 # API Provider（API 后端用）
│   │   ├── base.py                #   BaseProvider ABC
│   │   ├── kimi.py / deepseek.py / glm.py / minimax.py / default.py
│   │   ├── registry.py            #   Provider 注册表
│   │   └── test_providers.py      #   Provider 端到端测试
│   └── tasks/                     # 蒸馏任务
│       ├── base.py                #   BaseTask ABC
│       ├── query_response.py      #   query → response
│       ├── code_to_question.py    #   code → question
│       ├── text_to_response.py    #   prompt + text → response
│       ├── stackoverflow.py       #   StackOverflow 数据增强
│       └── registry.py            #   Task 注册表
├── configs/                       # API 配置文件
├── run.py                         # 统一 CLI 入口
├── run.sh                         # 通用 Shell 启动模板
└── requirements.txt
```

## 核心架构

### Backend 抽象

Engine 通过 Backend 接口调用 LLM，不关心底层是 API 还是 CLI：

```
Engine._process_item(item)
    → backend.call(item, task)
        ├── ApiBackend  → client_pool → provider → /chat/completions
        └── CliBackend  → subprocess  → claude --bare → stdout
    → task.process_result(item, content, thinking)
    → writer.write(result)
```

### 内置蒸馏任务

| 任务名 | 说明 | 输入字段 | 输出字段 |
|--------|------|----------|----------|
| `query_response` | 直接将 query 发给 LLM 获取回复 | `id`, `query` | `response`, `thinking` |
| `code_to_question` | 从代码片段生成高难度问题 | `text` | `prompt` |
| `text_to_response` | 将 prompt + text 拼接后生成回复 | `prompt`, `text` | `response` |
| `stackoverflow` | StackOverflow 数据增强 | `id`, `Post_Title`, `Post_Body`, `Answers` | `response`, `thinking` |

### 支持的 Provider（API 后端）

| Provider | 名称 | 特性 |
|----------|------|------|
| `kimi` | Moonshot Kimi | `reasoning_content` 字段提取 thinking |
| `dpsk` | DeepSeek | `reasoning_content` 或 `</think>` 标签解析 |
| `glm` | 智谱 GLM | `reasoning` 字段提取 thinking |
| `minimax` | MiniMax M2.5 | `<think>` 标签解析 |
| `default` | 标准 OpenAI | 通用兼容 |

### 支持的数据格式

| 格式 | 扩展名 | 特性 |
|------|--------|------|
| JSONL | `.jsonl` | 逐行流式读取，不全量加载 |
| Parquet | `.parquet` | 分批流式读取（`iter_batches`），metadata 快速计数 |

## CLI 参考

### 查看可用组件

```bash
python run.py --list
```

### API Backend 蒸馏

```bash
python run.py \
  --task <task_name> \
  --backend api \
  --provider <provider_name> \
  --config <config.json> \
  -i <input_file> -o <output_file> \
  [--temperature 0.7] [--top_p 0.95] [-w <workers>] \
  [--progress-threshold 100] [--max-retries 3]
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--task` | 必填 | 任务名 |
| `--backend` | `api` | 执行后端 (`api` 或 `cli`) |
| `--provider` | `default` | API Provider 名称 |
| `--config` | 必填 | API 配置文件 |
| `-w` / `--workers` | 自动 | 并发数 |
| `--temperature` | `0.7` | 采样温度 |
| `--top_p` | `None` | Nucleus sampling |
| `--timeout` | `72000` | API 请求超时（秒） |
| `--max-retries` | `3` | 单条最大重试 |
| `--progress-threshold` | `100` | 达到此百分比后停止 |
| `--split-max-lines` | `100000` | 输出分片最大行数 |
| `--batch-size` | `5000` | 流式加载批大小 |

### CLI Backend 蒸馏（Agent 模式）

```bash
python run.py \
  --task <task_name> \
  --backend cli \
  --cli-model <model_name> \
  [--cli-cmd claude] \
  [--agent-instructions /path/to/agent.md] \
  -i <input_file> -o <output_file> \
  [-w 4] [--cli-timeout 600]
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--backend cli` | - | 使用 CLI 后端 |
| `--cli-cmd` | `claude` | CLI 可执行文件名或路径 |
| `--cli-model` | `sonnet` | 传给 CLI `--model` 的模型名 |
| `--agent-instructions` | 无 | Agent 指令 `.md` 文件路径（内容预置到每个 prompt） |
| `--cli-timeout` | `600` | 单次 subprocess 超时（秒） |
| `--cli-extra-args` | 无 | 额外 CLI 参数（逗号分隔） |
| `-w` / `--workers` | `4` | 并发 subprocess 数 |

**环境变量支持**：

| 变量 | 说明 |
|------|------|
| `ANTHROPIC_BASE_URL` | 自定义 API 端点（自动传给 subprocess） |
| `ANTHROPIC_API_KEY` | API 密钥（自动传给 subprocess） |

### 健康检查

```bash
python run.py --health-check --config configs/config.json [--verbose]
```

### 后处理过滤

```bash
python run.py --filter keyword -i output.jsonl
python run.py --filter empty_response -i output.jsonl
```

### Provider 端到端测试

```bash
# 测试所有 provider
python -m distill_pipeline.providers.test_providers

# 只测试指定 provider
python -m distill_pipeline.providers.test_providers -p minimax glm

# 每个 provider 只测试 1 个端点
python -m distill_pipeline.providers.test_providers --max-endpoints 1
```

## 扩展开发

### 添加新 Backend

```python
# distill_pipeline/backends/my_backend.py
from .base import BaseBackend

class MyBackend(BaseBackend):
    name = "my_backend"

    async def call(self, item, task):
        messages = task.build_messages(item)
        # ... 自定义调用逻辑 ...
        return content, thinking
```

### 添加新 Provider

```python
# distill_pipeline/providers/my_provider.py
from .base import BaseProvider
from .registry import ProviderRegistry

@ProviderRegistry.register
class MyProvider(BaseProvider):
    name = "my_provider"

    def build_extra_body(self):
        return {"my_param": True}

    def extract_response(self, response):
        message = response.choices[0].message
        return message.content, None
```

### 添加新 Task

```python
# distill_pipeline/tasks/my_task.py
from .base import BaseTask
from .registry import TaskRegistry

@TaskRegistry.register
class MyTask(BaseTask):
    name = "my_task"

    def get_id(self, item):
        return str(item["id"])

    def build_messages(self, item):
        return [{"role": "user", "content": item["question"]}]

    def process_result(self, item, content, thinking):
        item["answer"] = content
        return item

    def validate_item(self, item):
        return "id" in item and "question" in item
```

### 添加新 DataLoader

```python
# distill_pipeline/dataloader/csv_loader.py
from .base import BaseDataLoader
from .registry import DataLoaderRegistry

@DataLoaderRegistry.register
class CsvLoader(BaseDataLoader):
    @property
    def supported_extensions(self):
        return [".csv"]

    def _iter_raw(self, file_path):
        import csv
        with open(file_path) as f:
            for row in csv.DictReader(f):
                yield dict(row)

    def count(self, file_path):
        return sum(1 for _ in self.load(file_path))
```

## 与原项目的对应关系

| 原脚本 | 新框架等价命令 |
|--------|---------------|
| `gen_game_query_response.py` | `--task query_response --backend api --provider glm` |
| `gen_text.py` | `--task code_to_question --backend api --provider default` |
| `gen_response.py` | `--task text_to_response --backend api --provider default` |
| `batch_enhance_parallel.py` | `--task stackoverflow --backend cli --cli-model sonnet --agent-instructions agent.md` |
| `check_health.py` | `--health-check --config xxx` |
| `filter.py` | `--filter keyword -i xxx` |
| `check_data.py` | `--filter empty_response -i xxx` |

## API 配置格式

**新格式**（推荐）—— concurrency 在每个 API 对象内：

```json
{
  "apis": [
    {
      "api_key": "sk-xxx",
      "base_url": "https://api.example.com/v1",
      "model": "gpt-4",
      "concurrency": 10
    }
  ]
}
```

**旧格式** —— concurrency 作为单独数组：

```json
{
  "apis": [
    {"api_key": "sk-xxx", "base_url": "https://api.example.com/v1", "model": "gpt-4"}
  ],
  "api_concurrencies": [10]
}
```

## 内置特性

- **双后端**：API 直接调用 或 CLI Agent subprocess，按需切换
- **流式加载**：JSONL/Parquet 逐行/分批流式读取，大文件秒级启动
- **断点续跑**：自动检测已处理数据，重启后跳过已完成项（单遍流式扫描）
- **去重**：基于 ID 字段自动去重，支持 `id` 和 `data_id` 两种字段
- **分片输出**：输出文件自动按行数分片（`.part0001.jsonl`, `.part0002.jsonl`...）
- **进度阈值**：达到指定完成百分比后自动停止
- **热重载**：API 后端运行中自动重载配置（每 30 分钟）
- **连接重试**：失败自动换 client / 重新调用（默认 3 次）
- **健康检查**：运行前测试所有 API 端点，只使用可用端点
- **Agent 指令**：CLI 后端支持加载 `.md` Agent 指令文件，自动去除 YAML frontmatter
- **Thinking 分离**：自动解析 `<think>...</think>` 标签或 `reasoning_content` 字段
