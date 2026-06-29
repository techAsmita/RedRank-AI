from __future__ import annotations

import re
from typing import List

YEARS_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
    re.IGNORECASE,
)

def extract_years(text: str) -> List[float]:
    return [float(x) for x in YEARS_PATTERN.findall(text)]

REMOTE_PATTERN = re.compile(r"\bremote\b", re.IGNORECASE)
HYBRID_PATTERN = re.compile(r"\bhybrid\b", re.IGNORECASE)
ONSITE_PATTERN = re.compile(r"\bon[- ]?site\b", re.IGNORECASE)

LEADERSHIP_PATTERN = re.compile(
    r"\b(lead|leader|leadership|mentor|mentoring|manage|manager|architect|ownership|own)\b",
    re.IGNORECASE,
)

PRODUCT_PATTERN = re.compile(
    r"\b(product mindset|customer|customer-focused|user experience|ownership|ship|shipping|production|end-to-end)\b",
    re.IGNORECASE,
)

COMMUNICATION_PATTERN = re.compile(
    r"\b(communication|communicate|collaboration|cross-functional|stakeholder|presentation)\b",
    re.IGNORECASE,
)

LEARNING_PATTERN = re.compile(
    r"\b(learning|curious|adaptable|growth mindset|continuous learning)\b",
    re.IGNORECASE,
)

DEGREE_PATTERN = re.compile(
    r"\b(b\.?tech|b\.?e|bachelor|m\.?tech|m\.?s|master|phd|doctorate)\b",
    re.IGNORECASE,
)

def extract_degrees(text: str) -> List[str]:
    return list(dict.fromkeys(DEGREE_PATTERN.findall(text)))
