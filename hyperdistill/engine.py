"""
Core async distillation engine.

Orchestrates the pipeline:
  DataLoader (streaming) -> Task -> Backend -> OutputWriter

Supports two backend modes:
  - ApiBackend: AsyncOpenAI /chat/completions (original)
  - CliBackend: subprocess calling claude CLI (agent mode)

Features:
- Streaming data loading — never loads entire input into memory
- Sliding window concurrency — submit and harvest continuously, never stalls
- Semaphore-based concurrency control
- Progress bar with tqdm
- Early stop at configurable threshold
- Retry with rotation on errors
"""

import asyncio
from typing import Any, Dict, List, Optional, Set

from tqdm import tqdm

from .backends.base import BaseBackend
from .dataloader import get_loader
from .output_writer import OutputWriter
from .tasks.base import BaseTask
from .utils import log


class DistillEngine:
    """Core engine that runs the distillation pipeline.

    The engine is backend-agnostic: it delegates the actual LLM call
    to a BaseBackend instance (API or CLI).

    Uses a sliding-window approach: items are submitted continuously
    and completed tasks are harvested as soon as they finish. This
    avoids the "batch stall" problem where a few slow items block
    the entire batch.
    """

    def __init__(
        self,
        task: BaseTask,
        backend: BaseBackend,
        writer: OutputWriter,
        input_file: str,
        max_workers: int = 10,
        progress_threshold: int = 95,
        max_retries: int = 3,
        required_fields: Optional[List[str]] = None,
        max_text_length: Optional[int] = None,
        batch_size: int = 5000,
    ):
        """Initialize the engine.

        Args:
            task: The distillation task to run.
            backend: The execution backend (API or CLI).
            writer: Output writer for results.
            input_file: Path to input data file.
            max_workers: Maximum concurrent requests.
            progress_threshold: Stop at this % completion.
            max_retries: Max retries per item on failure.
            required_fields: Required fields for data loading filter.
            max_text_length: Max text length for data loading filter.
            batch_size: Unused (kept for CLI compatibility). Concurrency is
                controlled entirely by max_workers via semaphore.
        """
        self.task = task
        self.backend = backend
        self.writer = writer
        self.input_file = input_file
        self.max_workers = max_workers
        self.progress_threshold = progress_threshold
        self.max_retries = max_retries
        self.required_fields = required_fields
        self.max_text_length = max_text_length

    async def _process_item(
        self,
        item: Dict[str, Any],
        sem: asyncio.Semaphore,
    ) -> Optional[Dict[str, Any]]:
        """Process a single data item through the pipeline.

        Args:
            item: The data item to process.
            sem: Semaphore for concurrency control.

        Returns:
            The processed result dict, or None on failure.
        """
        async with sem:
            for retry in range(self.max_retries):
                try:
                    content, thinking = await self.backend.call(item, self.task)
                    result = self.task.process_result(item, content, thinking)

                    if result is None:
                        # Only log retry message if this is not the first attempt
                        if retry > 0:
                            log(
                                f"Invalid result for item {self.task.get_id(item)}, "
                                f"retrying ({retry + 1}/{self.max_retries})"
                            )
                        continue

                    # Auto-inject 'id' field if not present
                    if "id" not in result:
                        result["id"] = self.task.get_id(item)

                    return result

                except Exception as e:
                    error_name = type(e).__name__
                    item_id = self.task.get_id(item)

                    # Only log retry message if this is not the first attempt
                    if retry > 0:
                        if "APIConnectionError" in error_name or "Connection" in str(e):
                            log(
                                f"Connection error for {item_id}, "
                                f"retrying ({retry + 1}/{self.max_retries}): "
                                f"{error_name}"
                            )
                        elif "TimeoutError" in error_name or "Timeout" in str(e):
                            log(
                                f"Timeout for {item_id}, "
                                f"retrying ({retry + 1}/{self.max_retries})"
                            )
                        else:
                            log(f"Error for {item_id}: {error_name}: {e}")
                    continue

        return None

    def _stream_items(self):
        """Stream input items, applying task expansion, validation and dedup filtering.

        Yields:
            Items that need processing.
        """
        loader = get_loader(
            self.input_file,
            required_fields=self.required_fields,
            max_text_length=self.max_text_length,
        )

        total_expanded = 0
        skipped = 0

        for item in loader.load(self.input_file):
            # Expand item into multiple items if task supports it
            expanded_items = self.task.expand_items(item)

            for expanded_item in expanded_items:
                # Validate each expanded item
                if not self.task.validate_item(expanded_item):
                    continue

                total_expanded += 1
                item_id = self.task.get_id(expanded_item)

                # Check if already processed
                if item_id in self.writer.processed_ids:
                    skipped += 1
                    continue

                yield expanded_item

        log(f"Stream complete: {total_expanded} valid items, {skipped} already processed")

    async def run(self) -> None:
        """Run the full distillation pipeline with sliding-window concurrency.

        Instead of batching items and waiting for a whole batch to complete,
        this uses a sliding window:
        1. Submit items as fast as the semaphore allows (up to max_workers in-flight)
        2. Continuously harvest completed tasks in the background
        3. Never stall waiting for a whole batch — if one item is slow,
           the rest keep flowing

        This avoids the "batch stall at 5000" problem.
        """
        import time

        # Step 1: Get fast input count for resume progress check
        log(f"Loading input data from: {self.input_file}")
        loader = get_loader(
            self.input_file,
            required_fields=self.required_fields,
            max_text_length=self.max_text_length,
        )
        input_total = loader.count_fast(self.input_file)
        log(f"Input file: ~{input_total} items (fast count)")

        # Step 2: Load resume state
        self.writer.load_resume_state(input_total=input_total, task=self.task)

        if self.writer.should_skip:
            log(f"Skipping: already >= {self.progress_threshold}% complete")
            return

        # Step 3: Sliding window — submit & harvest concurrently
        sem = asyncio.Semaphore(self.max_workers)
        log(f"Starting generation: {self.max_workers} workers, backend={self.backend.name}")

        pending: Set[asyncio.Task] = set()
        processed_count = 0
        submitted_count = 0
        stop_flag = False

        # Track resume baseline for global progress
        resumed_count = len(self.writer.processed_ids)
        start_time = time.time()

        pbar = tqdm(desc="Processing", unit="item", postfix={
            'global': f'0/{input_total}',
            'progress': '0.0%',
            'eta': 'N/A'
        })

        for item in self._stream_items():
            if stop_flag:
                break

            # Submit new task
            t = asyncio.create_task(self._process_item(item, sem))
            pending.add(t)
            submitted_count += 1

            # Harvest any completed tasks (non-blocking)
            done_tasks = {t for t in pending if t.done()}
            for done_task in done_tasks:
                pending.discard(done_task)
                pbar.update(1)
                result = done_task.result()
                if result:
                    self.writer.write(result)
                    processed_count += 1
                    self._update_progress_bar(pbar, processed_count, resumed_count,
                                             input_total, start_time)
                    if self._should_stop(processed_count, resumed_count, input_total):
                        stop_flag = True
                        break

            # If we have too many in-flight tasks, wait for at least one to finish
            # This prevents unbounded memory growth from pending tasks
            while len(pending) >= self.max_workers * 2 and not stop_flag:
                # Wait for the first task to complete
                done, pending = await asyncio.wait(
                    pending, return_when=asyncio.FIRST_COMPLETED
                )
                for done_task in done:
                    pbar.update(1)
                    result = done_task.result()
                    if result:
                        self.writer.write(result)
                        processed_count += 1
                        self._update_progress_bar(pbar, processed_count, resumed_count,
                                                 input_total, start_time)
                        if self._should_stop(processed_count, resumed_count, input_total):
                            stop_flag = True
                            break

        # Drain all remaining pending tasks
        if pending and not stop_flag:
            log(f"Draining {len(pending)} remaining tasks...")
            for done_task in asyncio.as_completed(pending):
                result = await done_task
                pbar.update(1)
                if result:
                    self.writer.write(result)
                    processed_count += 1
                    self._update_progress_bar(pbar, processed_count, resumed_count,
                                             input_total, start_time)
                    if self._should_stop(processed_count, resumed_count, input_total):
                        break
        elif pending and stop_flag:
            # Cancel remaining tasks on early stop
            log(f"Early stop: cancelling {len(pending)} remaining tasks")
            for t in pending:
                t.cancel()
            # Wait for cancellations to propagate
            await asyncio.gather(*pending, return_exceptions=True)

        pbar.close()
        log(f"Generation completed. Processed {processed_count}/{submitted_count} items.")

    def _update_progress_bar(self, pbar, processed_count: int, resumed_count: int,
                             input_total: int, start_time: float) -> None:
        """Update progress bar with global progress information.

        Args:
            pbar: tqdm progress bar instance.
            processed_count: Number of items processed in this session.
            resumed_count: Number of items already processed (from resume).
            input_total: Total number of items to process.
            start_time: Start time of the processing (for ETA calculation).
        """
        import time

        # Calculate global progress
        global_processed = resumed_count + processed_count
        global_progress = (global_processed / input_total * 100) if input_total > 0 else 0

        # Calculate ETA
        elapsed = time.time() - start_time
        current_speed = processed_count / elapsed if elapsed > 0 else 0
        remaining = input_total - global_processed
        eta_seconds = remaining / current_speed if current_speed > 0 else 0

        # Format ETA as HH:MM:SS
        if eta_seconds > 0 and eta_seconds < 86400 * 365:  # Less than 1 year
            hours = int(eta_seconds // 3600)
            minutes = int((eta_seconds % 3600) // 60)
            seconds = int(eta_seconds % 60)
            eta_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            eta_str = "N/A"

        # Update postfix
        pbar.set_postfix({
            'global': f'{global_processed}/{input_total}',
            'progress': f'{global_progress:.1f}%',
            'eta': eta_str
        })

    def _should_stop(self, processed_count: int, resumed_count: int, input_total: int) -> bool:
        """Check if we should stop early based on global progress threshold.

        Args:
            processed_count: Number of items processed in this session.
            resumed_count: Number of items already processed (from resume).
            input_total: Total number of items in the input file.

        Returns:
            True if global progress >= progress_threshold, False otherwise.
        """
        if self.progress_threshold >= 100 or input_total == 0:
            return False

        global_processed = resumed_count + processed_count
        global_progress = (global_processed / input_total) * 100
        return global_progress >= self.progress_threshold
