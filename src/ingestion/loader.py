"""
loader.py
---------
Streaming JSONL loader for RedRank AI.

Design decisions:
- Generator-based: yields one record at a time, never loads full file into memory.
- Robust: skips malformed lines with logging instead of crashing.
- Reusable: works for any JSONL file, not just candidates.
- Progress logging: reports every N records so long jobs stay observable.
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Generator

import yaml

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Config loader ─────────────────────────────────────────────────────────────
def load_config(config_path: str = "configs/settings.yaml") -> dict:
    """Load YAML config from disk."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── Core streaming loader ─────────────────────────────────────────────────────
def stream_jsonl(
    file_path: str | Path,
    log_every: int = 1000,
) -> Generator[dict, None, None]:
    """
    Stream records from a JSONL file one at a time.

    Args:
        file_path: Path to the .jsonl file.
        log_every: Log progress every N records.

    Yields:
        dict: One parsed JSON record per line.

    Design:
        - Uses a generator so memory stays flat regardless of file size.
        - Skips and logs malformed lines instead of crashing the pipeline.
        - Counts yielded vs skipped records for observability.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"JSONL file not found: {file_path}")

    if file_path.suffix not in {".jsonl", ".json"}:
        logger.warning("File extension is not .jsonl — proceeding anyway: %s", file_path)

    yielded = 0
    skipped = 0

    logger.info("Starting stream: %s", file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            # Skip blank lines silently
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                skipped += 1
                logger.warning("Skipping malformed line %d: %s", line_number, e)
                continue

            if not isinstance(record, dict):
                skipped += 1
                logger.warning("Skipping non-dict record at line %d", line_number)
                continue

            yielded += 1

            if yielded % log_every == 0:
                logger.info("Streamed %d records (skipped %d so far)...", yielded, skipped)

            yield record

    logger.info(
        "Stream complete — yielded: %d | skipped: %d | total lines: %d",
        yielded,
        skipped,
        yielded + skipped,
    )


# ── JSON loader (for sample files) ───────────────────────────────────────────
def load_json(file_path: str | Path) -> list[dict]:
    """
    Load a standard JSON file (list of records) fully into memory.
    Use only for small sample files during development.

    Args:
        file_path: Path to the .json file.

    Returns:
        List of raw record dicts.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    logger.info("Loading JSON file: %s", file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a list of records, got {type(data)}")

    logger.info("Loaded %d records from %s", len(data), file_path)
    return data
