"""
Output writer with partitioned JSONL files, deduplication, and resume support.

Handles:
- Loading previously processed output for dedup/resume (single-pass scan).
- Splitting output into .partNNNN.jsonl files when they exceed max lines.
- Progress tracking and early-stop threshold.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .utils import log


class OutputWriter:
    """Manages partitioned JSONL output with dedup and resume."""

    def __init__(
        self,
        output_file: str,
        split_max_lines: int = 100000,
        id_fields: Optional[List[str]] = None,
        progress_threshold: int = 95,
    ):
        """Initialize the output writer.

        Args:
            output_file: Path to the base output file.
            split_max_lines: Maximum lines per part file.
            id_fields: Field names to check for unique ID (tried in order).
                       Defaults to ['id', 'data_id'].
            progress_threshold: Stop if this % of input is already processed.
        """
        self.output_file = output_file
        self.split_max_lines = split_max_lines
        self.id_fields = id_fields or ["id", "data_id"]
        self.progress_threshold = progress_threshold

        self.output_path = Path(output_file)
        self.output_part_index = 1
        self.output_part_lines = 0

        self.processed_ids: Set[str] = set()
        self.should_skip = False

        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_item_id(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract the unique ID from a data item by checking id_fields in order."""
        for field in self.id_fields:
            val = data.get(field)
            if val is not None:
                return str(val)
        return None

    def _get_part_path(self, part_index: int) -> Path:
        """Get the path for a specific part file."""
        return self.output_path.with_name(
            f"{self.output_path.stem}.part{part_index:04d}{self.output_path.suffix}"
        )

    def _discover_output_files(self) -> Tuple[List[Path], List[int]]:
        """Discover all existing output files (base + parts)."""
        output_dir = self.output_path.parent
        part_pattern = re.compile(
            rf"^{re.escape(self.output_path.stem)}\.part(\d+){re.escape(self.output_path.suffix)}$"
        )

        output_files: List[Path] = []
        part_indices: List[int] = []

        for path in sorted(output_dir.glob(
            f"{self.output_path.stem}.part*{self.output_path.suffix}"
        )):
            output_files.append(path)
            match = part_pattern.match(path.name)
            if match:
                part_indices.append(int(match.group(1)))

        # Also check the base output file
        if self.output_path.exists():
            output_files.insert(0, self.output_path)

        return output_files, part_indices

    def load_resume_state(self, input_total: int = 0) -> None:
        """Load processed outputs from existing files for resume/dedup.

        Uses a single-pass streaming scan per file — never reads an entire
        output file into memory at once.

        Args:
            input_total: Total number of valid input items (for progress check).
        """
        output_files, part_indices = self._discover_output_files()

        if not output_files:
            self.should_skip = False
            log("No existing output files found, starting fresh")
            return

        # Single-pass: stream each file, collect unique IDs and count lines per file
        unique_ids: Set[str] = set()
        file_line_counts: Dict[Path, int] = {}

        for path in output_files:
            log(f"Scanning resume state from {path}")
            line_count = 0
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        line_count += 1
                        try:
                            data = json.loads(line)
                            uid = self._get_item_id(data)
                            if uid:
                                unique_ids.add(uid)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                log(f"Error reading {path}: {e}")

            file_line_counts[path] = line_count
            log(f"  {line_count} lines, {len(unique_ids)} unique IDs so far")

        # Check progress threshold
        if input_total > 0:
            total_processed = len(unique_ids)
            progress = (total_processed / input_total) * 100
            log(f"Resume progress: {total_processed}/{input_total} ({progress:.1f}%)")

            if progress >= self.progress_threshold:
                log(f"Already processed >= {self.progress_threshold}% ({progress:.1f}%), skipping")
                self.should_skip = True
                return

        self.should_skip = False
        self.processed_ids = unique_ids

        # Determine current part index and line count
        if part_indices:
            self.output_part_index = max(part_indices)
            part_path = self._get_part_path(self.output_part_index)
            self.output_part_lines = file_line_counts.get(part_path, 0)
        else:
            self.output_part_index = 1
            self.output_part_lines = 0

        # Roll over if current part is full
        if self.output_part_lines >= self.split_max_lines:
            self.output_part_index += 1
            self.output_part_lines = 0

        log(
            f"Resume: {len(self.processed_ids)} unique outputs, "
            f"next part {self.output_part_index:04d}, "
            f"lines in current part {self.output_part_lines}"
        )

    def write(self, result: Dict[str, Any]) -> None:
        """Write a single result to the output file.

        Automatically handles part file switching when max lines is reached.

        Args:
            result: The result dict to write.
        """
        # Ensure output directory exists
        output_dir = os.path.dirname(self.output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Switch part file if needed
        if self.output_part_lines >= self.split_max_lines:
            old_part = self.output_part_index
            self.output_part_index += 1
            self.output_part_lines = 0
            log(f"Switch output: part {old_part:04d} -> {self.output_part_index:04d}")

        part_path = self._get_part_path(self.output_part_index)
        line = json.dumps(result, ensure_ascii=False) + "\n"

        with open(part_path, "a", encoding="utf-8") as f:
            f.write(line)
        self.output_part_lines += 1

        # Track the ID to avoid duplicates in the current run
        uid = self._get_item_id(result)
        if uid:
            self.processed_ids.add(uid)
