"""Test data loader supporting JSON, YAML and Excel files.

All data files live under the ``testdata`` directory. The loader caches parsed
files so repeated access within a run is cheap.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import openpyxl
import yaml

from utils.logger import get_logger

log = get_logger("data_loader")

_DATA_DIR = Path(__file__).resolve().parent.parent / "testdata"


class DataLoader:
    """Loads externalized test data from JSON / YAML files."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or _DATA_DIR

    @lru_cache(maxsize=64)
    def _read(self, filename: str) -> Any:
        path = self.data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Test data file not found: {path}")

        log.debug("Loading test data file: %s", path)
        with path.open("r", encoding="utf-8") as fh:
            if path.suffix.lower() in {".yaml", ".yml"}:
                return yaml.safe_load(fh)
            if path.suffix.lower() == ".json":
                return json.load(fh)
        raise ValueError(f"Unsupported data file type: {path.suffix}")

    def load(self, filename: str) -> Any:
        """Load and return the full contents of a data file."""
        return self._read(filename)

    def get(self, filename: str, key: str, default: Any = None) -> Any:
        """Return a top-level key from a data file."""
        data = self._read(filename)
        if isinstance(data, dict):
            return data.get(key, default)
        return default

    @lru_cache(maxsize=32)
    def load_excel(self, filename: str, sheet: str | None = None) -> tuple[dict[str, Any], ...]:
        """Load an ``.xlsx`` sheet as a tuple of row dicts.

        The first row is treated as the header. Returns a tuple (hashable, so it
        can be cached) of ``{header: value}`` dicts, one per data row.
        """
        path = self.data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Test data file not found: {path}")

        log.debug("Loading Excel test data file: %s (sheet=%s)", path, sheet)
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
        try:
            worksheet = workbook[sheet] if sheet else workbook.active
            rows = list(worksheet.iter_rows(values_only=True))
        finally:
            workbook.close()

        if not rows:
            return ()

        headers = [str(h) for h in rows[0]]
        return tuple(
            {headers[i]: row[i] for i in range(len(headers))}
            for row in rows[1:]
            if any(cell is not None for cell in row)
        )

