# HyperDistill — Project Context

## Project Location
`/volume/pt-coder/users/tuney/Script/Hyperdistill/`

## Overview
Modular LLM data distillation framework supporting dual execution backends: API (AsyncOpenAI) and CLI (subprocess agent via `claude --bare`).

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
- **backends/**: BaseBackend ABC with ApiBackend and CliBackend implementations
- **agents/**: Agent loading, registry, YAML frontmatter parsing for CLI backend
- **skills/**: Skill loading, registry, dynamic injection for CLI backend
- **dataloader/**: Streaming JSONL/Parquet loaders with auto-detection by extension
- **providers/**: API provider implementations (Kimi, DeepSeek, GLM, MiniMax, Default)
- **tasks/**: Task implementations (query_response, code_to_question, text_to_response, stackoverflow, multiturn_distill, multiturn_all_distill, synthesize_cli_thinking, synthesize_cli_content)
- **engine.py**: Sliding-window async concurrency engine
- **output_writer.py**: Partitioned JSONL output with streaming resume/dedup
- **client_pool.py**: Concurrent client pool with random selection and hot-reload

## Design Decisions
- Registry pattern for extensibility (Task/Provider/DataLoader/Agent/Skill)
- Agent system with YAML frontmatter metadata and model override support
- Skill system with reusable capabilities injectable into agent prompts
- MiniMax thinking extraction from `<think>` tags in content
- Sliding-window concurrency to prevent batch stalling
- OutputWriter memory optimization (stores only processed_ids set)
- CliBackend uses asyncio.create_subprocess_exec for non-blocking execution

## Configuration
- `configs/config_{provider}.json` - API endpoint configurations
- `agents/*.md` - Agent definitions with YAML frontmatter
- `skills/*.md` - Skill definitions with YAML frontmatter

## CLI Usage
```bash
# API backend
python run.py --task <task> --backend api --provider <provider> --config <config.json> -i <input> -o <output>

# CLI backend with agent/skill system
python run.py --task <task> --backend cli --agent-name <agent> --agents-dir ./agents --skills <skill1>,<skill2> --skills-dir ./skills -i <input> -o <output>

# CLI backend (legacy mode)
python run.py --task <task> --backend cli --cli-model <model> --agent-instructions <agent.md> -i <input> -o <output>
```

## Development Workflow

### Core Principles

Development follows a pragmatic approach prioritizing code quality and user documentation over process overhead. The primary requirement is maintaining README.md as the single source of truth for users.

### Mandatory Requirements

When adding new functionality:

1. **Implementation**
   - Follow existing patterns (Registry pattern, ABC inheritance, async/await)
   - Add comprehensive docstrings for all public APIs
   - Include inline comments for non-trivial logic

2. **Documentation**
   - Update `README.md` with feature description, CLI parameters, and usage examples
   - This is the only strictly required documentation update
   - Users discover functionality through README.md exclusively

3. **Dependencies**
   - Update `requirements.txt` when adding new dependencies

### Optional Requirements (Judgment-Based)

The following are recommended but not mandatory. Developers should assess based on complexity and criticality:

**Testing**
- Write tests for complex logic and core functionality
- Simple wrappers and utility functions may skip tests
- Decision criterion: Would breakage affect multiple users?

**Detailed Documentation**
- Create `docs/*.md` only when README.md is insufficient
- Required for: complex systems, extensive configuration options, architectural explanations
- Most features require only README.md + docstrings

**Examples**
- Add to `examples/` only when demonstration is necessary
- Skip for straightforward features adequately covered in README.md

### Explicitly Not Required

- Updating CLAUDE.md (only for major architectural changes)
- Creating tests for every function
- Adding examples for every feature
- Exhaustive documentation beyond README.md

### Minimal Development Flow

```bash
# 1. Implement feature
vim hyperdistill/tasks/new_task.py
# Add docstrings

# 2. Update README.md
vim README.md
# Add to task list, CLI parameters, usage example

# 3. Verify functionality
python run.py --task new_task -i test.jsonl -o out.jsonl

# 4. Commit
git commit -m "Add new_task"
```

### Documentation Reading Strategy for AI Assistants

**Primary Source**
- Always read `README.md` first to understand overall structure and functionality

**Secondary Sources (On-Demand)**
- `docs/AGENT_SKILL_SYSTEM.md` - When working with Agent/Skill system
- `docs/DEVELOPMENT.md` - When understanding historical context is necessary
- `docs/SYNTHESIZE_CLI_CONTENT.md` - When developing similar task implementations
- Other docs - Only when specifically relevant to current work

**Anti-Pattern**
- Reading all documentation files on every interaction (information overload)

### Documentation Hierarchy

Priority order for documentation efforts:

1. README.md - User entry point, mandatory updates
2. Code docstrings - Developer reference, mandatory for public APIs
3. docs/ detailed documentation - Complex features only
4. tests/ - Critical functionality only
5. examples/ - Non-trivial use cases only

### When to Create Detailed Documentation

Create documentation in `docs/` only when:

1. System complexity exceeds README.md capacity (e.g., Agent/Skill system)
2. Multiple configuration options require detailed explanation
3. Internal mechanisms need architectural documentation
4. Design decisions require rationale documentation

Standard features require only README.md entries and code docstrings.

## Project Structure
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
git commit -m "Add my_new_task"
```

## Project Structure
```
Hyperdistill/
├── .claude/
│   └── CLAUDE.md                # Project context (this file)
├── README.md                    # User documentation (primary entry point)
├── run.py / run.sh              # Entry points
├── requirements.txt
├── docs/                        # Documentation
│   ├── README.md
│   ├── AGENT_SKILL_SYSTEM.md
│   ├── DEVELOPMENT.md
│   └── IMPLEMENTATION_SUMMARY.md
├── tests/                       # Test suite
│   ├── README.md
│   ├── test_agent_skill_system.py
│   └── test_providers.py
├── examples/                    # Usage examples
│   ├── README_AGENT_QA.md
│   └── run_qa_agent.sh
├── agents/                      # Agent definitions
├── skills/                      # Skill definitions
├── configs/                     # API configurations
└── hyperdistill/            # Core package
    ├── agents/
    ├── skills/
    ├── backends/
    ├── providers/
    ├── tasks/
    └── dataloader/
```

## Related Documentation
- `README.md` - Primary user documentation
- `docs/DEVELOPMENT.md` - Development history
- `docs/AGENT_SKILL_SYSTEM.md` - Agent/Skill system documentation
- `tests/README.md` - Test suite documentation
- `examples/README_AGENT_QA.md` - Agent Q&A examples
- `examples/README_AGENT_QA.md` — Agent Q&A example documentation
- Original project: `/volume/pt-coder/users/tuney/Script/raw2qa_new/`
- StackOverflow data: `/volume/pt-coder/users/tuney/pretrain_data/stackoverflow/`
