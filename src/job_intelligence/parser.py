"""
parser.py
---------

Deterministic Job Description parser.

Responsibilities
----------------
- Accept raw job description text
- Clean and normalize text
- Delegate extraction to the extractor
- Return a structured JobIntent

This module contains NO ranking logic.
NO embeddings.
NO similarity search.
NO LLM calls.
"""

from __future__ import annotations

from src.job_intelligence.extractor import extract_job_intent
from src.job_intelligence.models import JobIntent


def parse_job_description(raw_text: str) -> JobIntent:
    """
    Parse a raw job description into a structured JobIntent.
    """

    raw_text = raw_text.strip()

    return extract_job_intent(raw_text)