"""
Skill Loader - Load and parse skill definition files
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import yaml


@dataclass
class Skill:
    """Represents a Claude Code skill definition."""
    name: str
    content: str
    description: Optional[str] = None
    tools: Optional[List[str]] = None
    metadata: Optional[Dict] = None

    def __str__(self):
        parts = [f"Skill(name={self.name}"]
        if self.description:
            parts.append(f", description={self.description[:50]}...")
        if self.tools:
            parts.append(f", tools={','.join(self.tools)}")
        parts.append(")")
        return "".join(parts)


class SkillLoader:
    """Load skill definitions from markdown files with YAML frontmatter."""

    @staticmethod
    def load(file_path: str) -> Skill:
        """Load a skill from a markdown file.

        Format:
        ```markdown
        ---
        name: review-pr
        description: Review a GitHub pull request
        tools: [Bash, Read, Write]
        ---

        # Skill instructions
        ...skill content...
        ```

        Args:
            file_path: Path to the skill .md file

        Returns:
            Skill object with parsed metadata and content

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If frontmatter is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Skill file not found: {file_path}")

        content = path.read_text(encoding="utf-8")

        # Parse YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)

        if not frontmatter_match:
            # No frontmatter, use filename as name
            name = path.stem
            return Skill(
                name=name,
                content=content.strip(),
            )

        frontmatter_str = frontmatter_match.group(1)
        body = frontmatter_match.group(2).strip()

        try:
            frontmatter = yaml.safe_load(frontmatter_str) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter in {file_path}: {e}")

        # Extract known fields
        name = frontmatter.pop("name", path.stem)
        description = frontmatter.pop("description", None)
        tools = frontmatter.pop("tools", None)

        # Store remaining fields in metadata
        metadata = frontmatter if frontmatter else None

        return Skill(
            name=name,
            content=body,
            description=description,
            tools=tools,
            metadata=metadata,
        )

    @staticmethod
    def load_directory(directory: str) -> Dict[str, Skill]:
        """Load all skill files from a directory.

        Args:
            directory: Path to directory containing .md skill files

        Returns:
            Dict mapping skill names to Skill objects
        """
        path = Path(directory)
        if not path.exists() or not path.is_dir():
            raise ValueError(f"Directory not found: {directory}")

        skills = {}
        for file_path in path.glob("*.md"):
            try:
                skill = SkillLoader.load(str(file_path))
                skills[skill.name] = skill
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")

        return skills
