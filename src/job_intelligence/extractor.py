"""
extractor.py
------------

Deterministic extraction of recruiter intent.

This module converts raw JD text into a structured JobIntent.

No LLMs.
No embeddings.
No ranking.
"""

from __future__ import annotations

import re

from src.job_intelligence.models import (
    JobIntent,
)
from src.job_intelligence.patterns import (
    extract_years,
    LEADERSHIP_PATTERN,
    PRODUCT_PATTERN,
    COMMUNICATION_PATTERN,
    LEARNING_PATTERN,
)
from src.job_intelligence.taxonomy import (
    all_known_skills,
    get_category,
)


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def extract_job_intent(raw_text: str) -> JobIntent:
    raw_text = raw_text.strip()

    intent = JobIntent(raw_text=raw_text)

    _extract_metadata(intent, raw_text)
    _extract_technical(intent, raw_text)
    _extract_career(intent, raw_text)
    _extract_behavior(intent, raw_text)

    return intent


# ---------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------

def _extract_metadata(intent: JobIntent, text: str) -> None:
    """
    Lightweight metadata extraction.
    """

    title_match = re.search(
        r"(machine learning engineer|ml engineer|data scientist|software engineer|ai engineer)",
        text,
        re.IGNORECASE,
    )

    if title_match:
        intent.metadata.title = title_match.group(1)


# ---------------------------------------------------------------------
# Technical
# ---------------------------------------------------------------------

def _extract_technical(intent: JobIntent, text: str) -> None:

    text_lower = text.lower()

    found_skills = []

    categories = set()

    for skill in all_known_skills():
        if re.search(rf"\b{re.escape(skill)}\b", text_lower):
            found_skills.append(skill)

            category = get_category(skill)

            if category:
                categories.add(category)

    intent.technical.required_skills = sorted(found_skills)

    intent.technical.skill_categories = sorted(categories)

    years = extract_years(text)

    if years:
        intent.technical.minimum_years = min(years)

    intent.technical.python_required = "python" in found_skills

    intent.technical.retrieval = "retrieval" in categories

    intent.technical.evaluation = "evaluation" in categories

    intent.technical.mlops = "mlops" in categories

    intent.technical.cloud_required = "cloud" in categories

    intent.technical.production_ai = (
        "production" in text_lower
        or "production-grade" in text_lower
        or "production systems" in text_lower
    )


# ---------------------------------------------------------------------
# Career
# ---------------------------------------------------------------------

def _extract_career(intent: JobIntent, text: str) -> None:

    years = extract_years(text)

    if years:
        intent.career.minimum_experience_years = min(years)

    lower = text.lower()

    if "startup" in lower:
        intent.career.startup_background = True

    if "enterprise" in lower:
        intent.career.enterprise_background = True

    if "research" in lower:
        intent.career.research_background = True

    if re.search(r"\b(manage|manager|management|director|vp|head of)\b", text, re.IGNORECASE):
        intent.career.management_background = True


# ---------------------------------------------------------------------
# Behaviour
# ---------------------------------------------------------------------

def _extract_behavior(intent: JobIntent, text: str) -> None:

    intent.behavior.ownership = bool(
        LEADERSHIP_PATTERN.search(text)
    )

    intent.behavior.product_mindset = bool(
        PRODUCT_PATTERN.search(text)
    )

    intent.behavior.communication = bool(
        COMMUNICATION_PATTERN.search(text)
    )

    intent.behavior.learning_mindset = bool(
        LEARNING_PATTERN.search(text)
    )

    lower = text.lower()

    intent.behavior.cross_functional = (
        "cross-functional" in lower
    )

    intent.behavior.customer_focus = (
        "customer" in lower
    )

    intent.behavior.problem_solving = (
        "problem solving" in lower
        or "problem-solving" in lower
    )

    intent.behavior.ambiguity_tolerance = (
        "ambiguity" in lower
    )