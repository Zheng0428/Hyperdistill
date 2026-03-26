"""
Skill Registry - Centralized skill management
"""

from pathlib import Path
from typing import Dict, Optional
from .skill_loader import Skill, SkillLoader


class SkillRegistry:
    """Central registry for managing skills."""

    _skills: Dict[str, Skill] = {}

    @classmethod
    def register(cls, skill: Skill):
        """Register a skill."""
        cls._skills[skill.name] = skill

    @classmethod
    def get(cls, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return cls._skills.get(name)

    @classmethod
    def load_from_directory(cls, directory: str):
        """Load all skills from a directory."""
        skills = SkillLoader.load_directory(directory)
        for skill in skills.values():
            cls.register(skill)

    @classmethod
    def load_from_file(cls, file_path: str):
        """Load a single skill from a file."""
        skill = SkillLoader.load(file_path)
        cls.register(skill)

    @classmethod
    def list_skills(cls) -> list:
        """List all registered skill names."""
        return list(cls._skills.keys())

    @classmethod
    def clear(cls):
        """Clear all registered skills."""
        cls._skills.clear()
