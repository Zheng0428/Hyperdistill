"""
Agent Loader - Load and parse agent definition files
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import yaml


@dataclass
class Agent:
    """Represents a Claude Code agent definition."""
    name: str
    content: str
    model: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict] = None

    def __str__(self):
        parts = [f"Agent(name={self.name}"]
        if self.model:
            parts.append(f", model={self.model}")
        if self.description:
            parts.append(f", description={self.description}")
        parts.append(")")
        return "".join(parts)


class AgentLoader:
    """Load agent definitions from markdown files with YAML frontmatter."""

    @staticmethod
    def load(file_path: str) -> Agent:
        """Load an agent from a markdown file.

        Format:
        ```markdown
        ---
        name: stackoverflow-enhancer
        model: sonnet
        description: Enhance StackOverflow Q&A data
        ---

        # Your task
        ...agent instructions...
        ```

        Args:
            file_path: Path to the agent .md file

        Returns:
            Agent object with parsed metadata and content

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If frontmatter is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Agent file not found: {file_path}")

        content = path.read_text(encoding="utf-8")

        # Parse YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)

        if not frontmatter_match:
            # No frontmatter, use filename as name
            name = path.stem
            return Agent(
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
        model = frontmatter.pop("model", None)
        description = frontmatter.pop("description", None)

        # Store remaining fields in metadata
        metadata = frontmatter if frontmatter else None

        return Agent(
            name=name,
            content=body,
            model=model,
            description=description,
            metadata=metadata,
        )

    @staticmethod
    def load_directory(directory: str) -> Dict[str, Agent]:
        """Load all agent files from a directory.

        Args:
            directory: Path to directory containing .md agent files

        Returns:
            Dict mapping agent names to Agent objects
        """
        path = Path(directory)
        if not path.exists() or not path.is_dir():
            raise ValueError(f"Directory not found: {directory}")

        agents = {}
        for file_path in path.glob("*.md"):
            try:
                agent = AgentLoader.load(str(file_path))
                agents[agent.name] = agent
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")

        return agents
