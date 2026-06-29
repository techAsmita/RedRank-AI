from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from src.ingestion.models import Candidate
from src.features.preprocessing import (
    normalize_title,
    normalize_skills,
    normalize_company,
    duration_in_months,
)

logger = logging.getLogger(__name__)


@dataclass
class CandidateFeatures:
    """Structured raw features extracted from a Candidate. No scores — only facts."""
    candidate_id: Optional[str] = None
    name: Optional[str] = None

    total_experience_months: int = 0
    total_experience_years: float = 0.0
    number_of_jobs: int = 0
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    career_start_year: Optional[int] = None
    is_currently_employed: bool = False

    ai_experience_months: int = 0
    ai_titles: list = field(default_factory=list)

    normalized_skills: list = field(default_factory=list)
    skill_count: int = 0

    highest_degree: Optional[str] = None
    education_fields: list = field(default_factory=list)
    institutions: list = field(default_factory=list)

    certification_count: int = 0
    certification_names: list = field(default_factory=list)

    language_count: int = 0
    speaks_english: bool = False

    profile_score: Optional[float] = None
    is_open_to_work: bool = False
    notice_period_days: Optional[int] = None
    last_active_days: Optional[int] = None
    has_github: bool = False
    has_portfolio: bool = False

    profile_completeness: float = 0.0


AI_KEYWORDS = {
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "reinforcement learning", "llm", "generative ai",
    "transformer", "neural network", "data science", "ai", "artificial intelligence",
    "mlops", "feature engineering", "model training",
}

DEGREE_RANK = {
    "phd": 5, "doctorate": 5,
    "m.tech": 4, "mtech": 4, "m.s": 4, "ms": 4, "mba": 4, "masters": 4, "m.e": 4,
    "b.tech": 3, "btech": 3, "b.e": 3, "be": 3, "b.s": 3, "bs": 3, "bachelors": 3,
    "diploma": 2,
    "12th": 1, "high school": 1,
}


def _is_ai_role(title: Optional[str], description: Optional[str]) -> bool:
    text = f"{title or ''} {description or ''}".lower()
    return any(kw in text for kw in AI_KEYWORDS)


def _highest_degree(education: list) -> Optional[str]:
    best = None
    best_rank = -1
    for edu in education:
        degree = (edu.degree or "").lower().strip()
        rank = DEGREE_RANK.get(degree, 0)
        if rank > best_rank:
            best_rank = rank
            best = edu.degree
    return best


def _compute_completeness(candidate: Candidate) -> float:
    checks = [
        bool(candidate.profile.name),
        bool(candidate.profile.email),
        bool(candidate.profile.current_title),
        bool(candidate.profile.location),
        bool(candidate.profile.summary),
        bool(candidate.experience),
        bool(candidate.education),
        bool(candidate.skills.all_skills),
        bool(candidate.redrob.linkedin_url),
        bool(candidate.redrob.github_url or candidate.redrob.portfolio_url),
    ]
    return round(sum(checks) / len(checks), 2)


def extract_features(candidate: Candidate) -> CandidateFeatures:
    """Extract raw observable features from a Candidate object."""
    features = CandidateFeatures()
    features.candidate_id = candidate.profile.candidate_id
    features.name = candidate.profile.name

    total_months = 0
    ai_months = 0
    ai_titles = []
    career_years = []

    for exp in candidate.experience:
        months = duration_in_months(exp.start_date, exp.end_date)
        if months is not None:
            total_months += months
            if _is_ai_role(exp.title, exp.description):
                ai_months += months
                if exp.title:
                    ai_titles.append(normalize_title(exp.title))
        if exp.start_date:
            try:
                career_years.append(int(exp.start_date[:4]))
            except (ValueError, TypeError):
                pass

    features.total_experience_months = total_months
    features.total_experience_years = round(total_months / 12, 1)
    features.number_of_jobs = len(candidate.experience)
    features.ai_experience_months = ai_months
    features.ai_titles = list(set(t for t in ai_titles if t))
    features.career_start_year = min(career_years) if career_years else None

    for exp in candidate.experience:
        if exp.is_current:
            features.current_title = normalize_title(exp.title)
            features.current_company = normalize_company(exp.company)
            features.is_currently_employed = True
            break

    if not features.current_title:
        features.current_title = normalize_title(candidate.profile.current_title)
        features.current_company = normalize_company(candidate.profile.current_company)

    features.normalized_skills = normalize_skills(candidate.skills.all_skills)
    features.skill_count = len(features.normalized_skills)

    features.highest_degree = _highest_degree(candidate.education)
    features.education_fields = [e.field_of_study for e in candidate.education if e.field_of_study]
    features.institutions = [e.institution for e in candidate.education if e.institution]

    features.certification_count = len(candidate.certifications)
    features.certification_names = [c.name for c in candidate.certifications if c.name]

    features.language_count = len(candidate.languages)
    features.speaks_english = any(
        (lang.name or "").lower() in {"english", "en"}
        for lang in candidate.languages
    )

    features.profile_score = candidate.redrob.profile_score
    features.is_open_to_work = bool(candidate.redrob.is_open_to_work)
    features.notice_period_days = candidate.redrob.notice_period_days
    features.last_active_days = candidate.redrob.last_active_days
    features.has_github = bool(candidate.redrob.has_github)
    features.has_portfolio = bool(candidate.redrob.has_portfolio)

    features.profile_completeness = _compute_completeness(candidate)

    return features
