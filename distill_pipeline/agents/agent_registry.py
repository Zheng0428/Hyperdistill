"""
Agent Registry - Centralized agent management
"""

from pathlib import Path
from typing import Dict, Optional
from .agent_loader import Agent, AgentLoader


class AgentRegistry:
    """Central registry for managing agents."""

    _agents: Dict[str, Agent] = {}

    @classmethod
    def register(cls, agent: Agent):
        """Register an agent."""
        cls._agents[agent.name] = agent

    @classmethod
    def get(cls, name: str) -> Optional[Agent]:
        """Get an agent by name."""
        return cls._agents.get(name)

    @classmethod
    def load_from_directory(cls, directory: str):
        """Load all agents from a directory."""
        agents = AgentLoader.load_directory(directory)
        for agent in agents.values():
            cls.register(agent)

    @classmethod
    def load_from_file(cls, file_path: str):
        """Load a single agent from a file."""
        agent = AgentLoader.load(file_path)
        cls.register(agent)

    @classmethod
    def list_agents(cls) -> list:
        """List all registered agent names."""
        return list(cls._agents.keys())

    @classmethod
    def clear(cls):
        """Clear all registered agents."""
        cls._agents.clear()
