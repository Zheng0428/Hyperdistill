# Agent and Skill System

## Overview

The hyperdistill now supports a modular agent and skill system for the CLI backend. This allows you to:

- **Define agents**: Pre-configured agent personas with specific instructions and models
- **Define skills**: Reusable capabilities that can be loaded into agents
- **Organize configurations**: Keep agent and skill definitions in separate `.md` files
- **Mix and match**: Combine agents with different skills for different tasks

## Directory Structure

```
Hyperdistill/
├── agents/                          # Your agent definitions
│   ├── example_agent.md
│   └── stackoverflow_enhancer.md
├── skills/                          # Your skill definitions
│   ├── code_analyzer.md
│   └── data_validator.md
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

Skills are defined similarly:

```markdown
---
name: code-analyzer
description: Analyze code for issues
tools: [Read, Grep, Glob]
---

# Skill Instructions

This skill helps analyze code for...
```

### Skill Frontmatter Fields

- `name`: Skill identifier (required, defaults to filename)
- `description`: Brief description (optional)
- `tools`: List of Claude Code tools the skill uses (optional)
- Any other fields are stored in `metadata`

## CLI Usage

### Using Agents

```bash
# Use agent by name (from agents directory)
python run.py --task stackoverflow --backend cli \
  --agent-name stackoverflow-enhancer \
  --agents-dir ./agents \
  -i input.jsonl -o output.jsonl

# Legacy: Use agent instructions file directly
python run.py --task stackoverflow --backend cli \
  --agent-instructions ./agents/stackoverflow_enhancer.md \
  -i input.jsonl -o output.jsonl
```

### Using Skills

```bash
# Load skills with an agent
python run.py --task query_response --backend cli \
  --agent-name example-agent \
  --agents-dir ./agents \
  --skills code-analyzer,data-validator \
  --skills-dir ./skills \
  -i input.jsonl -o output.jsonl
```

### CLI Parameters

| Parameter | Description |
|-----------|-------------|
| `--agent-name NAME` | Name of agent to load from registry |
| `--agents-dir DIR` | Directory containing agent .md files (auto-registered) |
| `--skills LIST` | Comma-separated skill names to load |
| `--skills-dir DIR` | Directory containing skill .md files (auto-registered) |
| `--agent-instructions PATH` | Legacy: direct path to agent .md file |

## Programmatic Usage

```python
from hyperdistill.agents import AgentLoader, AgentRegistry
from hyperdistill.skills import SkillLoader, SkillRegistry
from hyperdistill.backends.cli_backend import CliBackend

# Load agents and skills
AgentRegistry.load_from_directory("agents")
SkillRegistry.load_from_directory("skills")

# Create backend with agent and skills
backend = CliBackend(
    agent_name="stackoverflow-enhancer",
    skills=["code-analyzer", "data-validator"],
    agents_dir="agents",
    skills_dir="skills",
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

- **Auto-registration**: When `--agents-dir` or `--skills-dir` is specified, all `.md` files are automatically loaded into registries
- **On-demand loading**: Agents/skills are retrieved by name when needed
- **Validation**: Files with invalid YAML frontmatter will be skipped with a warning

## Examples

See:
- `examples/agent_example.py` - Complete usage examples
- `test_agent_skill_system.py` - Test suite
- `agents/` - Example agent definitions
- `skills/` - Example skill definitions

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
   - Group related agents/skills in subdirectories (future feature)
   - Version control your agent/skill definitions

4. **Naming Conventions**
   - Use kebab-case for names: `stackoverflow-enhancer`, `code-analyzer`
   - Be descriptive: `data-validator` not `validator`
   - Avoid spaces in filenames

## Backward Compatibility

The system is fully backward compatible with the legacy `--agent-instructions` parameter. Existing scripts will continue to work without modification.

## Future Enhancements

Potential improvements:
- Subdirectory support for organizing agents/skills
- Agent/skill versioning
- Skill dependencies
- Agent composition (agents that inherit from other agents)
- Remote agent/skill repositories
