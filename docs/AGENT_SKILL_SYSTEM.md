# Agent and Skill System

## Overview

The hyperdistill now supports a modular agent and skill system for the CLI backend. This allows you to:

- **Define agents**: Pre-configured agent personas with specific instructions and models
- **Define skills**: Reusable capabilities that can be loaded into agents
- **Organize configurations**: Follow Claude Code's project-level `.claude` layout
- **Mix and match**: Combine agents with different skills for different tasks

## Directory Structure

```
Hyperdistill/
├── .claude/
│   ├── agents/                      # Your agent definitions
│   │   ├── example-agent.md
│   │   └── stackoverflow-enhancer.md
│   └── skills/                      # Your Claude-style skills
│       ├── code-analyzer/
│       │   └── SKILL.md
│       └── data-validator/
│           └── SKILL.md
└── hyperdistill/
    ├── agents/                      # Agent system code
    │   ├── __init__.py
    │   ├── agent_loader.py
    │   └── agent_registry.py
    └── skills/                      # Skill system code
        ├── __init__.py
        ├── skill_loader.py
        └── skill_registry.py
```

## Agent File Format

Agents are defined in markdown files with YAML frontmatter:

```markdown
---
name: stackoverflow-enhancer
model: sonnet
description: Enhance StackOverflow Q&A
---

# Agent Instructions

You are a technical expert specializing in...

## Your Task
...
```

### Agent Frontmatter Fields

- `name`: Agent identifier (required, defaults to filename)
- `model`: Model to use (optional, overrides CLI `--cli-model`)
- `description`: Brief description (optional)
- Any other fields are stored in `metadata`

## Skill File Format

Skills follow Claude Code's directory-based format:

```markdown
.claude/skills/code-analyzer/SKILL.md
---
name: code-analyzer
description: Analyze code for issues
allowed-tools: [Read, Grep, Glob]
---

# Skill Instructions

This skill helps analyze code for...
```

### Skill Frontmatter Fields

- `name`: Skill identifier (required, defaults to directory name for `SKILL.md`)
- `description`: Brief description (optional)
- `allowed-tools`: List of Claude Code tools the skill uses (optional)
- Any other fields are stored in `metadata`

## CLI Usage

### Using Agents

```bash
# Use agent by name (defaults to ./.claude/agents)
python run.py --task stackoverflow --backend cli \
  --agent-name stackoverflow-enhancer \
  -i input.jsonl -o output.jsonl

# Legacy: Use agent instructions file directly
python run.py --task stackoverflow --backend cli \
  --agent-instructions ./.claude/agents/stackoverflow-enhancer.md \
  -i input.jsonl -o output.jsonl
```

### Using Skills

```bash
# Load skills with an agent
python run.py --task query_response --backend cli \
  --agent-name example-agent \
  --skills code-analyzer,data-validator \
  -i input.jsonl -o output.jsonl
```

### CLI Parameters

| Parameter | Description |
|-----------|-------------|
| `--agent-name NAME` | Name of agent to load from registry (defaults to `./.claude/agents`) |
| `--agents-dir DIR` | Directory containing agent `.md` files |
| `--skills LIST` | Comma-separated skill names to load (defaults to `./.claude/skills`) |
| `--skills-dir DIR` | Directory containing Claude-style skills directories |
| `--agent-instructions PATH` | Legacy: direct path to agent .md file |

## Programmatic Usage

```python
from hyperdistill.agents import AgentLoader, AgentRegistry
from hyperdistill.skills import SkillLoader, SkillRegistry
from hyperdistill.backends.cli_backend import CliBackend

# Load agents and skills
AgentRegistry.load_from_directory(".claude/agents")
SkillRegistry.load_from_directory(".claude/skills")

# Create backend with agent and skills
backend = CliBackend(
    agent_name="stackoverflow-enhancer",
    skills=["code-analyzer", "data-validator"],
    agents_dir=".claude/agents",
    skills_dir=".claude/skills",
)

# The backend will automatically:
# 1. Load the agent's instructions
# 2. Override the model if specified in agent
# 3. Inject skill instructions into prompts
```

## How It Works

### Prompt Construction

When processing an item, the CLI backend builds the prompt in this order:

1. **Agent instructions** (from agent file)
2. **Skill instructions** (from loaded skills)
   ```
   ## Available Skills
   ### Skill: code-analyzer
   Description: ...
   Tools: Read, Grep, Glob
   [skill content]
   ```
3. **Task messages** (from task.build_messages())

### Model Selection

Priority order:
1. Agent's `model` field (if specified in frontmatter)
2. CLI `--cli-model` flag
3. Default: `sonnet`

### Agent/Skill Loading

- **Auto-registration**: When `--agents-dir` or `--skills-dir` is specified, definitions are automatically loaded into registries
- **On-demand loading**: Agents/skills are retrieved by name when needed
- **Validation**: Files with invalid YAML frontmatter will be skipped with a warning
- **Compatibility**: `skills` supports both Claude-style `SKILL.md` directories and legacy flat `.md` files

## Examples

See:
- `examples/agent_example.py` - Complete usage examples
- `test_agent_skill_system.py` - Test suite
- `.claude/agents/` - Example agent definitions
- `.claude/skills/` - Example skill definitions

## Best Practices

1. **Agent Design**
   - Keep agents focused on specific domains (e.g., stackoverflow, code generation)
   - Use clear, structured instructions
   - Specify the model in frontmatter if it's critical to the agent's function

2. **Skill Design**
   - Make skills reusable across different agents
   - Document which tools the skill uses
   - Keep skills focused on specific capabilities

3. **Organization**
   - Use descriptive filenames (they become default names)
   - Keep project-scoped definitions under `.claude/agents` and `.claude/skills`
   - Version control your agent/skill definitions

4. **Naming Conventions**
   - Use kebab-case for names: `stackoverflow-enhancer`, `code-analyzer`
   - Be descriptive: `data-validator` not `validator`
   - Avoid spaces in filenames

## Backward Compatibility

The system is fully backward compatible with the legacy `--agent-instructions` parameter. Existing scripts will continue to work without modification.

## Future Enhancements

Potential improvements:
- Agent/skill versioning
- Skill dependencies
- Agent composition (agents that inherit from other agents)
- Remote agent/skill repositories
