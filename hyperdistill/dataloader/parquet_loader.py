"""
Parquet file data loader with batch streaming support.

Requires pyarrow: pip install pyarrow
"""

from typing import Any, Dict, Iterator, List

from .base import BaseDataLoader
from ..utils import log


class ParquetLoader(BaseDataLoader):
    """Load data from Apache Parquet files.

    Uses batch streaming via RecordBatchReader to avoid loading
    the entire Parquet file into memory at once.
    """

    def __init__(self, batch_size: int = 4096, **kwargs):
        """
        Args:
            batch_size: Number of rows per batch when streaming.
            **kwargs: Passed to BaseDataLoader.
        """
        super().__init__(**kwargs)
        self.batch_size = batch_size

    @property
    def supported_extensions(self) -> List[str]:
        return [".parquet"]

    def _iter_raw(self, file_path: str) -> Iterator[Dict[str, Any]]:
        """Stream rows from the Parquet file in batches."""
        try:
            import pyarrow.parquet as pq
        except ImportError:
            raise ImportError(
                "pyarrow is required for Parquet support. Install with: pip install pyarrow"
            )

        metadata = pq.read_metadata(file_path)
        total_rows = metadata.num_rows
        log(f"Streaming Parquet: {file_path} ({total_rows} rows, batch_size={self.batch_size})")

        parquet_file = pq.ParquetFile(file_path)
        for batch in parquet_file.iter_batches(batch_size=self.batch_size):
            table = batch.to_pydict()
            columns = list(table.keys())
            num_rows = len(table[columns[0]]) if columns else 0

            for i in range(num_rows):
                row = {col: table[col][i] for col in columns}
                yield row

    def count(self, file_path: str) -> int:
        """Count filtered items (streams through the file)."""
        total = 0
        for _ in self.load(file_path):
            total += 1
        return total

    def count_fast(self, file_path: str) -> int:
        """Fast row count from Parquet metadata (no filtering)."""
        try:
            import pyarrow.parquet as pq
        except ImportError:
            raise ImportError("pyarrow is required for Parquet support.")

        metadata = pq.read_metadata(file_path)
        return metadata.num_rows
