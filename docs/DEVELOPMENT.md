# Distill Pipeline — 开发过程文档

## 项目背景

原项目 `/volume/pt-coder/users/tuney/Script/raw2qa_new/` 包含 7+ 个 Python 脚本和 14+ 个 Shell 脚本，用于 LLM 数据蒸馏。这些脚本共享 ~80% 的代码（API client 管理、断点续跑/去重、输出分片、进度追踪），但在输入格式、prompt 构建、provider 差异、过滤规则上各不相同，导致维护困难、新增任务容易出错。

决定在 `/volume/pt-coder/users/tuney/Script/distill_pipeline/` 创建模块化、可扩展的统一框架。

---

## 开发阶段

### Phase 1：核心框架搭建

**目标**：建立模块化的项目骨架，统一替代 raw2qa_new 下的重复脚本。

**设计决策**：
- Registry 模式注册 Task / Provider / DataLoader，新增只需一个文件+注册
- 保持与原有 config.json 格式完全兼容（新旧两种 concurrency 格式）
- 统一 CLI 入口 `run.py`，通过 `--task` + `--provider` 组合替代多个脚本

**创建的模块**：

| 模块 | 文件 | 职责 |
|------|------|------|
| 工具 | `utils.py`, `config.py` | 日志、ID 生成、配置加载 |
| DataLoader | `dataloader/{base,jsonl_loader,parquet_loader,registry}.py` | 数据加载，按扩展名自动匹配 |
| Provider | `providers/{base,kimi,deepseek,glm,default,registry}.py` | 封装不同 API 的 `extra_body` 和响应解析 |
| Task | `tasks/{base,query_response,code_to_question,text_to_response,registry}.py` | 定义蒸馏任务的 prompt 构建和结果处理 |
| ClientPool | `client_pool.py` | 异步客户端池：按 concurrency 展开、随机选择、热重载 |
| OutputWriter | `output_writer.py` | 分片 JSONL 输出、去重、断点续跑 |
| Engine | `engine.py` | 核心异步引擎，串联各模块 |
| HealthCheck | `health_check.py` | API 端点健康检查 |
| Filters | `filters.py` | 关键词过滤、空响应清除 |

**入口文件**：
- `run.py` — 统一 CLI
- `run.sh` — 通用 Shell 启动模板（健康检查 + 蒸馏）

---

### Phase 2：添加 MiniMax Provider

**背景**：新增 MiniMax M2.5 模型支持。

**关键发现**：MiniMax 部署在 vLLM 上，`reasoning_content` 为 `None`，thinking 内容嵌入在 `content` 中的 `<think>...</think>` 标签里。

**实现**：
- 创建 `providers/minimax.py`
- 解析优先级：`reasoning_content` → `<think>...</think>` 标签 → `</think>` fallback
- `extra_body = {"chat_template_kwargs": {"thinking": True}}`

**测试工具**：创建 `providers/test_providers.py` 端到端测试脚本，自动扫描 `configs/config_{provider}.json`，对每个端点发送真实推理请求验证配置正确性。

---

### Phase 3：添加 StackOverflow 增强任务

**背景**：需要处理 StackOverflow 原始数据，增强为高质量技术 Q&A。

**输入格式**：包含 `Post_Id`, `Post_Title`, `Post_Body`(HTML), `Post_Tags`, `Answers`, `Comments` 等字段。

**实现**：
- 创建 `tasks/stackoverflow.py`
- System prompt 定义增强专家角色
- User prompt 模板嵌入源数据 JSON，指导模型提升难度和完整性
- `validate_item()` 要求有 `id` 字段

**同时移除**：删除了 YAML Task（`yaml_task.py` 和 `task_configs/`），简化架构。

---

### Phase 4：流式读取优化

**问题**：大文件（千万行）加载时 `load_all()` 全量读入内存，启动等待几分钟。

**改造**：

| 组件 | 之前 | 之后 |
|------|------|------|
| JsonlLoader | 全量读入 | 逐行 `yield`，打印文件大小 |
| ParquetLoader | `read_table()` 全量 | `iter_batches(batch_size=4096)` 分批流式 |
| BaseDataLoader | `load()` 返回 list | `load()` 返回 iterator，新增 `count_fast()` |
| OutputWriter | 两遍扫描（readlines + 反向去重） | 单遍流式扫描，只保留 `processed_ids` 集合 |
| Engine | `load_all()` → 全量创建 task | 流式迭代 + 分批提交 |

---

### Phase 5：Backend 抽象层（Agent 支持）

**背景**：需要支持通过 subprocess 调用 `claude` CLI 作为 agent 进行蒸馏，与原有 API 模式并存。

**架构设计**：

```
Engine._process_item(item)
    → backend.call(item, task)        # 统一接口
        ├── ApiBackend  → client_pool → provider → /chat/completions
        └── CliBackend  → asyncio.subprocess → claude --bare → stdout
    → task.process_result(item, content, thinking)
    → writer.write(result)
```

**新增文件**：
- `backends/base.py` — `BaseBackend` ABC，`async call(item, task) → (content, thinking)`
- `backends/api_backend.py` — 从 engine.py 提取原有 API 调用逻辑
- `backends/cli_backend.py` — 异步 subprocess 调用 CLI

**CliBackend 特性**：
- `asyncio.create_subprocess_exec` 异步调用，不阻塞事件循环
- 自动加载 `.md` agent 指令文件，去除 YAML frontmatter
- 自动解析 `<think>...</think>` 标签分离 thinking/content
- 支持 `ANTHROPIC_BASE_URL` / `ANTHROPIC_API_KEY` 环境变量传递
- 可配置 CLI 命令、超时、额外参数

**run.py 变更**：
- 新增 `--backend {api,cli}` 参数
- API 后端参数：`--provider`, `--config`, `--temperature` 等
- CLI 后端参数：`--cli-cmd`, `--cli-model`, `--agent-instructions`, `--cli-timeout`

---

### Phase 6：滑动窗口并发（修复 batch 卡住）

**问题**：batch_size=5000 时，在 ~4998 item 处稳定卡住。

**根因**：
1. `_drain_batch()` 必须等 5000 个 task **全部** 完成才返回
2. 少数慢请求（超时/重试）阻塞整个 batch
3. drain 期间不提交新任务，pipeline 断流

**解决方案**：改为滑动窗口并发：

```python
for item in stream:
    submit(item)                       # 立即提交
    harvest_done_tasks()               # 非阻塞收割已完成的
    while pending > 2 * max_workers:   # 背压控制
        await wait(FIRST_COMPLETED)    # 等最快那个完成就继续
```

**效果**：
- 不再有 batch 积攒，每个 item 立即提交
- 持续收割，慢请求不影响快请求
- `pending` 超过 `2 * max_workers` 时才阻塞，用 `FIRST_COMPLETED` 等待
- pipeline 永不断流

---

## 最终文件清单

```
distill_pipeline/
├── distill_pipeline/
│   ├── __init__.py
│   ├── config.py                    # API 配置加载
│   ├── utils.py                     # 日志、ID 生成
│   ├── engine.py                    # 核心引擎（滑动窗口并发）
│   ├── output_writer.py             # 分片输出 + 流式 resume
│   ├── client_pool.py               # 异步客户端池
│   ├── health_check.py              # API 健康检查
│   ├── filters.py                   # 关键词/空响应过滤
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── base.py                  # BaseBackend ABC
│   │   ├── api_backend.py           # API 后端（AsyncOpenAI）
│   │   └── cli_backend.py           # CLI 后端（subprocess agent）
│   ├── dataloader/
│   │   ├── __init__.py
│   │   ├── base.py                  # BaseDataLoader ABC
│   │   ├── jsonl_loader.py          # JSONL 流式加载
│   │   ├── parquet_loader.py        # Parquet 批流式加载
│   │   └── registry.py              # 按扩展名自动匹配
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py                  # BaseProvider ABC
│   │   ├── kimi.py / deepseek.py / glm.py / minimax.py / default.py
│   │   ├── registry.py              # Provider 注册表
│   │   └── test_providers.py        # Provider 端到端测试
│   └── tasks/
│       ├── __init__.py
│       ├── base.py                  # BaseTask ABC
│       ├── query_response.py        # query → response
│       ├── code_to_question.py      # code → question
│       ├── text_to_response.py      # prompt + text → response
│       ├── stackoverflow.py         # StackOverflow 增强
│       └── registry.py              # Task 注册表
├── configs/                         # API 配置文件
├── run.py                           # 统一 CLI 入口
├── run.sh                           # 通用 Shell 启动模板
├── README.md                        # 使用文档
├── DEVELOPMENT.md                   # 本文档
└── requirements.txt
```

## 使用快速参考

```bash
# API 模式
python run.py --task query_response --backend api --provider minimax \
  --config configs/config_minimax.json -i input.jsonl -o output.jsonl

# CLI Agent 模式
python run.py --task stackoverflow --backend cli --cli-model sonnet \
  --agent-instructions /path/to/agent.md -i input.jsonl -o output.jsonl -w 4

# 健康检查
python run.py --health-check --config configs/config.json

# Provider 测试
python -m distill_pipeline.providers.test_providers --max-endpoints 1

# 过滤
python run.py --filter keyword -i output.jsonl

# 查看所有组件
python run.py --list
```
