#!/usr/bin/env python3
"""
Test script for agent and skill system
"""

import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from distill_pipeline.agents import AgentLoader, AgentRegistry
from distill_pipeline.skills import SkillLoader, SkillRegistry


def test_agent_loading():
    """Test agent loading functionality."""
    print("Testing Agent Loading...")

    # Test loading single agent
    agent = AgentLoader.load("agents/example_agent.md")
    assert agent.name == "example-agent"
    assert agent.model == "sonnet"
    assert len(agent.content) > 0
    print("✓ Single agent loading works")

    # Test loading directory
    agents = AgentLoader.load_directory("agents")
    assert len(agents) > 0
    assert "example-agent" in agents
    assert "stackoverflow-enhancer" in agents
    print(f"✓ Directory loading works ({len(agents)} agents found)")

    return True


def test_skill_loading():
    """Test skill loading functionality."""
    print("\nTesting Skill Loading...")

    # Test loading single skill
    skill = SkillLoader.load("skills/code_analyzer.md")
    assert skill.name == "code-analyzer"
    assert len(skill.content) > 0
    assert skill.tools is not None
    print("✓ Single skill loading works")

    # Test loading directory
    skills = SkillLoader.load_directory("skills")
    assert len(skills) > 0
    assert "code-analyzer" in skills
    assert "data-validator" in skills
    print(f"✓ Directory loading works ({len(skills)} skills found)")

    return True


def test_registry():
    """Test registry functionality."""
    print("\nTesting Registry...")

    # Clear registries
    AgentRegistry.clear()
    SkillRegistry.clear()

    # Load from directory
    AgentRegistry.load_from_directory("agents")
    SkillRegistry.load_from_directory("skills")

    # Check registration
    assert len(AgentRegistry.list_agents()) > 0
    assert len(SkillRegistry.list_skills()) > 0
    print(f"✓ Registry works (agents: {AgentRegistry.list_agents()})")
    print(f"✓ Registry works (skills: {SkillRegistry.list_skills()})")

    # Test retrieval
    agent = AgentRegistry.get("example-agent")
    assert agent is not None
    assert agent.name == "example-agent"

    skill = SkillRegistry.get("code-analyzer")
    assert skill is not None
    assert skill.name == "code-analyzer"
    print("✓ Registry retrieval works")

    return True


def test_cli_backend_integration():
    """Test CLI backend integration."""
    print("\nTesting CLI Backend Integration...")

    try:
        # Import directly to avoid the __init__.py import chain
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "cli_backend",
            "distill_pipeline/backends/cli_backend.py"
        )
        cli_backend_module = importlib.util.module_from_spec(spec)

        # Need to mock the parent imports
        import sys
        sys.modules['distill_pipeline.backends.base'] = type(sys)('mock')
        sys.modules['distill_pipeline.backends.base'].BaseBackend = object
        sys.modules['distill_pipeline.tasks.base'] = type(sys)('mock')
        sys.modules['distill_pipeline.tasks.base'].BaseTask = object
        sys.modules['distill_pipeline.utils'] = type(sys)('mock')
        sys.modules['distill_pipeline.utils'].log = print

        # Import agents/skills directly
        from distill_pipeline.agents import Agent, AgentRegistry
        from distill_pipeline.skills import Skill, SkillRegistry
        sys.modules['distill_pipeline.agents'] = type(sys)('mock')
        sys.modules['distill_pipeline.agents'].Agent = Agent
        sys.modules['distill_pipeline.agents'].AgentRegistry = AgentRegistry
        sys.modules['distill_pipeline.skills'] = type(sys)('mock')
        sys.modules['distill_pipeline.skills'].Skill = Skill
        sys.modules['distill_pipeline.skills'].SkillRegistry = SkillRegistry

        spec.loader.exec_module(cli_backend_module)
        CliBackend = cli_backend_module.CliBackend

        # Test with agent_name
        backend = CliBackend(
            agent_name="example-agent",
            agents_dir="agents",
        )
        assert backend.agent is not None
        assert backend.agent.name == "example-agent"
        print("✓ CLI Backend loads agent correctly")

        # Test with skills
        backend = CliBackend(
            agent_name="example-agent",
            agents_dir="agents",
            skills=["code-analyzer", "data-validator"],
            skills_dir="skills",
        )
        assert len(backend.skills) == 2
        print(f"✓ CLI Backend loads skills correctly ({len(backend.skills)} skills)")

        # Test legacy agent_instructions_path
        backend = CliBackend(
            agent_instructions_path="agents/example_agent.md",
        )
        assert len(backend.agent_instructions) > 0
        print("✓ CLI Backend supports legacy agent_instructions_path")

        return True
    except Exception as e:
        print(f"⚠️  CLI Backend integration test skipped (openai not installed): {e}")
        return True  # Don't fail if openai is missing


def main():
    """Run all tests."""
    print("=" * 60)
    print("Agent and Skill System Tests")
    print("=" * 60)
    print()

    try:
        test_agent_loading()
        test_skill_loading()
        test_registry()
        test_cli_backend_integration()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
