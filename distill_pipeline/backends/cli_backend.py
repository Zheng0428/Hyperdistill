"""
CLI Backend — calls LLM via subprocess (e.g., claude CLI).

Uses asyncio.create_subprocess_exec for non-blocking subprocess calls.
Supports custom commands, agent instructions files, and environment variables.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base import BaseBackend
from ..tasks.base import BaseTask
from ..utils import log
from ..agents import Agent, AgentRegistry
from ..skills import Skill, SkillRegistry


class CliBackend(BaseBackend):
    """Backend that calls LLM via CLI subprocess (e.g., claude --bare).

    Features:
    - Async subprocess (does not block the event loop)
    - Configurable CLI command and model
    - Loads agent instructions from .md files (strips YAML frontmatter)
    - Passes environment variables (ANTHROPIC_BASE_URL, ANTHROPIC_API_KEY)
    - Parses <think>...</think> tags for thinking separation
    """

    name = "cli"

    def __init__(
        self,
        cli_cmd: str = "claude",
        model: str = "sonnet",
        agent_instructions_path: Optional[str] = None,
        timeout: int = 600,
        extra_env: Optional[Dict[str, str]] = None,
        cli_extra_args: Optional[List[str]] = None,
        agent_name: Optional[str] = None,
        skills: Optional[List[str]] = None,
        agents_dir: Optional[str] = None,
        skills_dir: Optional[str] = None,
    ):
        """
        Args:
            cli_cmd: The CLI executable name or path (default: 'claude').
            model: Model name passed via --model flag.
            agent_instructions_path: Path to agent .md file. If set, its
                content is prepended to every prompt. (Legacy, use agent_name instead)
            timeout: Subprocess timeout in seconds (default: 600 = 10min).
            extra_env: Additional environment variables for the subprocess.
            cli_extra_args: Extra CLI arguments (e.g., ['--verbose']).
            agent_name: Name of the agent to load from registry.
            skills: List of skill names to load from registry.
            agents_dir: Directory containing agent .md files (auto-registered).
            skills_dir: Directory containing skill .md files (auto-registered).
        """
        self.cli_cmd = cli_cmd
        self.model = model
        self.timeout = timeout
        self.extra_env = extra_env or {}
        self.cli_extra_args = cli_extra_args or []

        # Load agents/skills from directories if specified
        if agents_dir:
            AgentRegistry.load_from_directory(agents_dir)
            log(f"CLI Backend: loaded agents from {agents_dir}")
        if skills_dir:
            SkillRegistry.load_from_directory(skills_dir)
            log(f"CLI Backend: loaded skills from {skills_dir}")

        # Load agent from registry or legacy path
        self.agent: Optional[Agent] = None
        self.agent_instructions = ""

        if agent_name:
            self.agent = AgentRegistry.get(agent_name)
            if not self.agent:
                raise ValueError(f"Agent not found in registry: {agent_name}")
            self.agent_instructions = self.agent.content
            # Override model if agent specifies one
            if self.agent.model:
                self.model = self.agent.model
            log(f"CLI Backend: loaded agent '{agent_name}' ({len(self.agent_instructions)} chars)")
        elif agent_instructions_path:
            # Legacy: load from file directly
            self.agent_instructions = self._load_instructions(agent_instructions_path)
            log(f"CLI Backend: loaded agent instructions ({len(self.agent_instructions)} chars)")

        # Load skills from registry
        self.skills: List[Skill] = []
        if skills:
            for skill_name in skills:
                skill = SkillRegistry.get(skill_name)
                if not skill:
                    log(f"Warning: Skill not found in registry: {skill_name}")
                else:
                    self.skills.append(skill)
            if self.skills:
                log(f"CLI Backend: loaded {len(self.skills)} skill(s): {[s.name for s in self.skills]}")

        log(
            f"CLI Backend: cmd={self.cli_cmd}, model={self.model}, "
            f"timeout={self.timeout}s"
        )

    @staticmethod
    def _load_instructions(path: str) -> str:
        """Load agent instructions from a markdown file.

        Strips YAML frontmatter (content between --- markers) if present.

        Args:
            path: Path to the .md file.

        Returns:
            The instruction text with frontmatter removed.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Agent instructions file not found: {path}")

        content = p.read_text(encoding="utf-8")

        # Strip YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2].strip()

        return content

    def _build_prompt(self, item: Dict[str, Any], task: BaseTask) -> str:
        """Build the full prompt to pass to the CLI via stdin.

        If agent_instructions are loaded, prepend them.
        If skills are loaded, append them.
        Then append the user content from task.build_messages().

        Args:
            item: The data item.
            task: The task instance.

        Returns:
            The complete prompt string.
        """
        messages = task.build_messages(item)

        # Collect system and user parts
        parts = []

        # Add agent instructions
        if self.agent_instructions:
            parts.append(self.agent_instructions)

        # Add skills
        if self.skills:
            parts.append("\n## Available Skills\n")
            for skill in self.skills:
                parts.append(f"### Skill: {skill.name}")
                if skill.description:
                    parts.append(f"Description: {skill.description}")
                if skill.tools:
                    parts.append(f"Tools: {', '.join(skill.tools)}")
                parts.append(f"\n{skill.content}\n")

        # Add task messages
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system" and content:
                parts.append(content)
            elif role == "user" and content:
                parts.append(content)

        return "\n\n".join(parts)

    def _build_cmd(self) -> List[str]:
        """Build the CLI command list.

        Returns:
            e.g., ['claude', '--model', 'sonnet', '--bare']
        """
        cmd = [self.cli_cmd, "--model", self.model, "--bare"]
        cmd.extend(self.cli_extra_args)
        return cmd

    def _build_env(self) -> Dict[str, str]:
        """Build the environment dict for the subprocess."""
        env = os.environ.copy()
        env.update(self.extra_env)
        return env

    @staticmethod
    def _parse_output(output: str) -> Tuple[str, Optional[str]]:
        """Parse CLI output to separate content and thinking.

        Handles:
        1. <think>...</think> tags → thinking + content after tag
        2. </think> without <think> → thinking (before) + content (after)
        3. No tags → content only

        Args:
            output: Raw stdout from the CLI.

        Returns:
            (content, thinking) tuple.
        """
        output = output.strip()

        # Case 1: Full <think>...</think> tags
        if "<think>" in output and "</think>" in output:
            think_start = output.index("<think>") + len("<think>")
            think_end = output.index("</think>")
            thinking = output[think_start:think_end].strip()
            content = output[think_end + len("</think>"):].strip()
            return content, thinking

        # Case 2: </think> without opening <think>
        if "</think>" in output:
            parts = output.split("</think>", 1)
            thinking = parts[0].strip()
            content = parts[1].strip() if len(parts) > 1 else ""
            return content, thinking

        # Case 3: No thinking tags
        return output, None

    async def call(
        self,
        item: Dict[str, Any],
        task: BaseTask,
    ) -> Tuple[str, Optional[str]]:
        """Call the CLI subprocess and return (content, thinking).

        Steps:
        1. Build prompt from task + agent instructions
        2. Build CLI command
        3. Run async subprocess, pass prompt via stdin
        4. Parse stdout to extract content and thinking

        Raises:
            RuntimeError: If the CLI returns non-zero exit code.
            asyncio.TimeoutError: If the subprocess exceeds timeout.
        """
        prompt = self._build_prompt(item, task)
        cmd = self._build_cmd()
        env = self._build_env()

        # Async subprocess
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(input=prompt.encode("utf-8")),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise asyncio.TimeoutError(
                f"CLI subprocess timed out after {self.timeout}s"
            )

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        if proc.returncode != 0:
            raise RuntimeError(
                f"CLI exited with code {proc.returncode}: {stderr[:500]}"
            )

        if not stdout.strip():
            raise RuntimeError("CLI returned empty output")

        return self._parse_output(stdout)
