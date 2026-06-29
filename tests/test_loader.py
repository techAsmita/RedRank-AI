"""Tests for the streaming JSONL loader."""

import json
import tempfile
from pathlib import Path

from src.ingestion.loader import stream_jsonl, load_json


def test_load_json_sample():
    """Sample JSON file loads correctly."""
    records = load_json("data/sample/sample_candidates.json")
    assert isinstance(records, list)
    assert len(records) > 0
    assert isinstance(records[0], dict)


def test_stream_jsonl_basic():
    """JSONL stream yields correct number of records."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for i in range(5):
            f.write(json.dumps({"id": i, "name": f"Candidate {i}"}) + "\n")
        tmp_path = f.name

    records = list(stream_jsonl(tmp_path))
    assert len(records) == 5


def test_stream_jsonl_skips_malformed():
    """Malformed lines are skipped without crashing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write(json.dumps({"id": 1}) + "\n")
        f.write("THIS IS NOT JSON\n")
        f.write(json.dumps({"id": 2}) + "\n")
        tmp_path = f.name

    records = list(stream_jsonl(tmp_path))
    assert len(records) == 2
