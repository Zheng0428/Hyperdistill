# Distill Pipeline — Project Context

## Project Location
`/volume/pt-coder/users/tuney/Script/distill_pipeline/`

## What This Is
A modular LLM data distillation framework. Supports two execution backends: **API** (AsyncOpenAI) and **CLI** (subprocess agent like `claude --bare`).

## Architecture
```
Engine (sliding-window concurrency)
  → Backend.call(item, task)
      ├── ApiBackend  → ClientPool → Provider → /chat/completions
      └── CliBackend  → asyncio.subprocess → claude --bare
                      → Agent/Skill System → Prompt Builder
  → Task.process_result()
  → OutputWriter.write()
```

## Key Modules
- **backends/**: `BaseBackend` ABC → `ApiBackend`, `CliBackend`
- **agents/**: Agent loading, registry, YAML frontmatter parsing (CLI backend)
- **skills/**: Skill loading, registry, dynamic injection (CLI backend)
- **dataloader/**: Streaming JSONL/Parquet loaders (never full load), auto-detect by extension
- **providers/**: Kimi, DeepSeek, GLM, MiniMax, Default — each handles `extra_body` + response parsing
- **tasks/**: `query_response`, `code_to_question`, `text_to_response`, `stackoverflow`
- **engine.py**: Sliding-window async concurrency (fixed batch-stall bug at 5k items)
- **output_writer.py**: Partitioned JSONL output, single-pass streaming resume/dedup
- **client_pool.py**: Concurrency expansion, random selection, hot-reload
- **providers/test_providers.py**: End-to-end provider testing against real endpoints

## Important Design Decisions
- Registry pattern for Task/Provider/DataLoader/Agent/Skill — new ones just register
- Agent system: YAML frontmatter for metadata, supports model override
- Skill system: Reusable capabilities injected into agent prompts
- MiniMax thinking is in `<think>` tags inside content (not `reasoning_content`)
- Engine uses sliding window (not batch drain) to avoid stalling
- OutputWriter only stores `processed_ids` set, not full data objects
- CliBackend uses `asyncio.create_subprocess_exec` for non-blocking subprocess

## Config Files
- `configs/config_{provider}.json` — API endpoint configs
- `agents/*.md` — Agent definition files with YAML frontmatter
- `skills/*.md` — Skill definition files with YAML frontmatter
- Agent instructions loaded from `.md` files, YAML frontmatter auto-stripped

## CLI Entry Point
```bash
# API mode
python run.py --task <name> --backend api --provider <name> --config <json> -i <in> -o <out>

# CLI agent mode (with agent/skill system)
python run.py --task <name> --backend cli \
  --agent-name <agent> --agents-dir ./agents \
  --skills <skill1>,<skill2> --skills-dir ./skills \
  -i <in> -o <out>

# CLI agent mode (legacy)
python run.py --task <name> --backend cli --cli-model <model> --agent-instructions <md> -i <in> -o <out>
```

## Development Workflow

### 🚀 Adding New Features

**MANDATORY STEPS** (必须执行的步骤):

1. **Write Code**
   - Implement the feature in appropriate module
   - Follow existing patterns (Registry, ABC, etc.)
   - Add docstrings and comments

2. **Write Documentation** ⚠️ **CRITICAL - DO NOT SKIP**
   - Create/update documentation in `docs/`
   - **MUST update** `README.md` (root) - 用户总入口
   - Update `CLAUDE.md` if architecture changes
   - Add examples in `examples/` if applicable
   - Update module-specific docs

3. **Write Tests** ⚠️ **CRITICAL - DO NOT SKIP**
   - Add tests in `tests/`
   - Test all new functionality
   - Verify edge cases
   - Run existing tests to ensure no breakage

4. **Update Configuration**
   - Update `.gitignore` if needed
   - Update `requirements.txt` if new dependencies
   - Update CLI arguments in `run.py` if needed

### 📝 Documentation Checklist

When adding ANY new feature, **MUST** update:

- [ ] `README.md` (root) ⭐ **HIGHEST PRIORITY** - 用户入口文档
  - [ ] Update feature list
  - [ ] Update CLI parameters table
  - [ ] Update examples
  - [ ] Update architecture diagram if needed

- [ ] `docs/` directory
  - [ ] Create new doc or update existing
  - [ ] Add to `docs/README.md` index
  - [ ] Include usage examples
  - [ ] Document all parameters

- [ ] `CLAUDE.md` (this file) if:
  - [ ] Architecture changes
  - [ ] New modules added
  - [ ] Design decisions made

- [ ] `examples/`
  - [ ] Add working examples
  - [ ] Add example data if needed
  - [ ] Update example README

### 🧪 Testing Checklist

- [ ] Write unit tests in `tests/`
- [ ] Update `tests/README.md` if new test added
- [ ] Run all existing tests: `python tests/test_*.py`
- [ ] Test with real data
- [ ] Document test in test file docstring

### 📂 File Organization Rules

1. **Root directory**: Keep MINIMAL
   - Only: README.md, CLAUDE.md, run.py, run.sh, requirements.txt, .gitignore

2. **Documentation**: ALL in `docs/`
   - System docs, design docs, implementation notes
   - Each doc must be indexed in `docs/README.md`

3. **Tests**: ALL in `tests/`
   - Test files must start with `test_`
   - Include README explaining how to run

4. **Examples**: ALL in `examples/`
   - Working scripts and sample data
   - Include README for each example

5. **Code**: In `distill_pipeline/` package
   - Follow module structure
   - Use Registry pattern for extensibility

### 🔄 Standard Workflow Example

Example: Adding a new Task

```bash
# 1. Write code
vim distill_pipeline/tasks/my_new_task.py
# Use @TaskRegistry.register decorator

# 2. Write documentation (MANDATORY)
# 2a. Update root README (MOST IMPORTANT)
vim README.md
# - Add task to task table
# - Add usage example
# - Update architecture if needed

# 2b. Create detailed doc
vim docs/MY_NEW_TASK.md
# - Full description
# - All parameters
# - Examples
# - Best practices

# 2c. Update docs index
vim docs/README.md
# - Add link to new doc

# 2d. Update CLAUDE.md
vim CLAUDE.md
# - Add to Key Modules if significant

# 3. Write tests (MANDATORY)
vim tests/test_my_new_task.py
# - Test all functionality
# - Test edge cases

vim tests/README.md
# - Document new test

# 4. Add examples
vim examples/run_my_task.sh
vim examples/sample_my_task_input.jsonl

vim examples/README.md
# - Document new example

# 5. Run tests
python tests/test_my_new_task.py
python tests/test_agent_skill_system.py  # Ensure no breakage

# 6. Test with real data
bash examples/run_my_task.sh

# 7. Update requirements if needed
vim requirements.txt

# 8. Commit
git add .
git commit -m "Add my_new_task with full docs and tests"
```

### ⚠️ CRITICAL REMINDERS

1. **README.md 是用户的第一入口** - 必须及时更新
2. **所有新功能必须有文档** - 在 docs/ 目录
3. **所有新功能必须有测试** - 在 tests/ 目录
4. **保持主目录整洁** - 只放必要文件
5. **遵循现有模式** - Registry, ABC, 异步等
6. **写完整的 docstrings** - 包括参数、返回值、异常
7. **测试向后兼容性** - 确保旧功能不受影响

### 🎯 Documentation Priority Order

When time is limited, prioritize in this order:

1. **README.md** (root) ⭐⭐⭐ - HIGHEST - 用户第一看到的
2. **Code docstrings** ⭐⭐ - For developers
3. **docs/** detailed docs ⭐⭐ - For deep understanding
4. **examples/** ⭐ - For learning by doing
5. **tests/README.md** - For running tests

**但理想情况下，所有文档都应该完整！**

## Project Structure
```
distill_pipeline/
├── README.md                    # 用户文档（总入口）
├── CLAUDE.md                    # 本文件：AI 上下文
├── run.py / run.sh              # 主入口
├── requirements.txt
├── docs/                        # 📚 文档目录
│   ├── README.md               # 文档索引
│   ├── AGENT_SKILL_SYSTEM.md   # Agent/Skill 系统文档
│   ├── DEVELOPMENT.md          # 开发历史
│   └── IMPLEMENTATION_SUMMARY.md
├── tests/                       # 🧪 测试目录
│   ├── README.md
│   ├── test_agent_skill_system.py
│   └── test_providers.py
├── examples/                    # 💡 示例目录
│   ├── README_AGENT_QA.md
│   └── run_qa_agent.sh
├── agents/                      # Agent 定义文件
├── skills/                      # Skill 定义文件
├── configs/                     # API 配置
└── distill_pipeline/            # 核心包
    ├── agents/                  # Agent 系统代码
    ├── skills/                  # Skill 系统代码
    ├── backends/                # 执行后端
    ├── providers/               # API Providers
    ├── tasks/                   # 蒸馏任务
    └── dataloader/              # 数据加载器
```

## Related Files
- `docs/DEVELOPMENT.md` — Full development history with 6 phases
- `README.md` — User-facing documentation (总入口)
- `docs/AGENT_SKILL_SYSTEM.md` — Agent and skill system documentation
- `tests/README.md` — Test suite documentation
- `examples/README_AGENT_QA.md` — Agent Q&A example documentation
- Original project: `/volume/pt-coder/users/tuney/Script/raw2qa_new/`
- StackOverflow data: `/volume/pt-coder/users/tuney/pretrain_data/stackoverflow/`
