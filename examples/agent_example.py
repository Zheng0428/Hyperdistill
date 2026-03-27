#!/usr/bin/env python3
"""
Example: Using Agents and Skills with CLI Backend

This example demonstrates how to use the agent and skill system
with the CLI backend for data distillation.
"""

import sys
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from hyperdistill.agents import AgentLoader, AgentRegistry
from hyperdistill.skills import SkillLoader, SkillRegistry

AGENTS_DIR = os.path.join(PROJECT_ROOT, ".claude", "agents")
SKILLS_DIR = os.path.join(PROJECT_ROOT, ".claude", "skills")


def main():
    print("=" * 60)
    print("Agent and Skill System Example")
    print("=" * 60)
    print()

    # Example 1: Load a single agent
    print("1. Loading a single agent:")
    agent = AgentLoader.load(f"{AGENTS_DIR}/example-agent.md")
    print(f"   Loaded: {agent}")
    print(f"   Content length: {len(agent.content)} chars")
    print()

    # Example 2: Load all agents from directory
    print("2. Loading agents from directory:")
    agents = AgentLoader.load_directory(AGENTS_DIR)
    for name, agent in agents.items():
        print(f"   - {name}: {agent.description or 'No description'}")
    print()

    # Example 3: Load skills
    print("3. Loading skills:")
    skills = SkillLoader.load_directory(SKILLS_DIR)
    for name, skill in skills.items():
        print(f"   - {name}: {skill.description or 'No description'}")
        if skill.tools:
            print(f"     Tools: {', '.join(skill.tools)}")
    print()

    # Example 4: Using registry
    print("4. Using registry:")
    AgentRegistry.load_from_directory(AGENTS_DIR)
    SkillRegistry.load_from_directory(SKILLS_DIR)

    print(f"   Registered agents: {AgentRegistry.list_agents()}")
    print(f"   Registered skills: {SkillRegistry.list_skills()}")
    print()

    # Example 5: Retrieve from registry
    print("5. Retrieving from registry:")
    agent = AgentRegistry.get("stackoverflow-enhancer")
    if agent:
        print(f"   Agent: {agent.name}")
        print(f"   Model: {agent.model}")
        print(f"   Description: {agent.description}")

    skill = SkillRegistry.get("code-analyzer")
    if skill:
        print(f"   Skill: {skill.name}")
        print(f"   Tools: {skill.tools}")
    print()

    print("=" * 60)
    print("CLI Backend Usage Examples:")
    print("=" * 60)
    print()

    print("Example 1: Using agent from directory")
    print("  python run.py --task stackoverflow --backend cli \\")
    print("    --agent-name stackoverflow-enhancer \\")
    print("    -i input.jsonl -o output.jsonl")
    print()

    print("Example 2: Using agent with skills")
    print("  python run.py --task query_response --backend cli \\")
    print("    --agent-name example-agent \\")
    print("    --skills code-analyzer,data-validator \\")
    print("    -i input.jsonl -o output.jsonl")
    print()

    print("Example 3: Legacy agent instructions file")
    print("  python run.py --task stackoverflow --backend cli \\")
    print("    --agent-instructions ./.claude/agents/stackoverflow-enhancer.md \\")
    print("    -i input.jsonl -o output.jsonl")
    print()


if __name__ == "__main__":
    main()
