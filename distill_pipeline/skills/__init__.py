"""
Skill Management Module

Provides infrastructure for managing Claude Code skills that can be loaded
during CLI backend execution. Skills are defined in markdown files with
YAML frontmatter.
"""

from .skill_loader import SkillLoader, Skill
from .skill_registry import SkillRegistry

__all__ = ["SkillLoader", "Skill", "SkillRegistry"]
