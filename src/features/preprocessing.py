from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

TITLE_ALIASES: dict = {
    "sde": "software engineer",
    "sde-1": "software engineer",
    "sde-2": "senior software engineer",
    "sde1": "software engineer",
    "sde2": "senior software engineer",
    "mle": "machine learning engineer",
    "ml engineer": "machine learning engineer",
    "ai engineer": "machine learning engineer",
    "ds": "data scientist",
    "de": "data engineer",
    "backend dev": "backend engineer",
    "frontend dev": "frontend engineer",
    "full stack": "full stack engineer",
    "fullstack": "full stack engineer",
    "devops": "devops engineer",
    "pm": "product manager",
}

SKILL_ALIASES: dict = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "tf": "tensorflow",
    "k8s": "kubernetes",
    "gcp": "google cloud platform",
    "aws": "amazon web services",
    "azure": "microsoft azure",
    "pg": "postgresql",
    "mongo": "mongodb",
    "react.js": "react",
    "reactjs": "react",
    "node.js": "nodejs",
    "vue.js": "vue",
}

COMPANY_ALIASES: dict = {
    "google llc": "google",
    "alphabet": "google",
    "meta platforms": "meta",
    "facebook": "meta",
    "microsoft corporation": "microsoft",
    "amazon.com": "amazon",
    "amazon web services": "amazon",
}

DATE_FORMATS = [
    "%Y-%m",
    "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y",
    "%b %Y", "%B %Y", "%Y",
]

PROFICIENCY_MAP: dict = {
    "native": "native",
    "fluent": "fluent",
    "professional": "professional",
    "conversational": "conversational",
    "basic": "basic",
    "beginner": "basic",
    "advanced": "fluent",
    "intermediate": "conversational",
    "elementary": "basic",
}


def normalize_title(title: Optional[str]) -> Optional[str]:
    if not title:
        return None
    cleaned = re.sub(r"\s+", " ", title.lower().strip())
    return TITLE_ALIASES.get(cleaned, cleaned)


def normalize_skill(skill: Optional[str]) -> Optional[str]:
    if not skill:
        return None
    cleaned = re.sub(r"\s+", " ", skill.lower().strip())
    return SKILL_ALIASES.get(cleaned, cleaned)


def normalize_skills(skills: list) -> list:
    normalized = [normalize_skill(s) for s in skills if s]
    return list(dict.fromkeys(s for s in normalized if s))


def normalize_company(company: Optional[str]) -> Optional[str]:
    if not company:
        return None
    cleaned = re.sub(r"\s+", " ", company.lower().strip())
    return COMPANY_ALIASES.get(cleaned, cleaned)


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    date_str = date_str.strip()
    if date_str.lower() in {"present", "current", "now", "till date"}:
        return datetime.now()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def duration_in_months(start: Optional[str], end: Optional[str]) -> Optional[int]:
    start_dt = parse_date(start)
    end_dt = parse_date(end) if end else datetime.now()
    if start_dt is None or end_dt is None:
        return None
    if end_dt < start_dt:
        return None
    months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
    return max(0, months)


def normalize_location(location: Optional[str]) -> Optional[str]:
    if not location:
        return None
    return location.strip().title()


def normalize_proficiency(proficiency: Optional[str]) -> Optional[str]:
    if not proficiency:
        return None
    return PROFICIENCY_MAP.get(proficiency.lower().strip(), proficiency.lower().strip())


def clean_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
