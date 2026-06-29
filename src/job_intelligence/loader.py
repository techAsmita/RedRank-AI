"""
loader.py
---------

Utilities for loading job descriptions from disk.
"""

from pathlib import Path
from typing import Union


def load_job_description(path: Union[str, Path]) -> str:
    """
    Load a markdown or text job description.
    """

    path = Path(path)

    return path.read_text(
        encoding="utf-8"
    ).strip()