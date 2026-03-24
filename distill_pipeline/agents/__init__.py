"""
Agent Management Module

Provides infrastructure for managing Claude Code agents that can be used
during CLI backend execution. Agents are defined in markdown files with
YAML frontmatter for metadata.
"""

from .agent_loader import AgentLoader, Agent
from .agent_registry import AgentRegistry

__all__ = ["AgentLoader", "Agent", "AgentRegistry"]
