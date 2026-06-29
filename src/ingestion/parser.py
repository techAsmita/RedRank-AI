from __future__ import annotations

"""
parser.py
---------
Converts raw JSON dicts into typed Candidate objects.
"""

import logging
from typing import Optional

from pydantic import ValidationError

from src.ingestion.models import (
    Candidate,
    CandidateProfile,
    Certification,
    Education,
    Experience,
    Language,
    RedrobSignals,
    Skills,
)

logger = logging.getLogger(__name__)


def _parse_profile(raw: dict) -> CandidateProfile:
    return CandidateProfile(
        candidate_id=raw.get("candidate_id") or raw.get("id"),
        name=raw.get("name") or raw.get("full_name"),
        email=raw.get("email"),
        phone=raw.get("phone") or raw.get("mobile"),
        location=raw.get("location") or raw.get("city"),
        current_title=raw.get("current_title") or raw.get("title"),
        current_company=raw.get("current_company") or raw.get("company"),
        summary=raw.get("summary") or raw.get("about") or raw.get("bio"),
        years_of_experience=_safe_float(raw.get("years_of_experience")),
    )


def _parse_experience(raw_list: list) -> list[Experience]:
    if not isinstance(raw_list, list):
        return []
    result = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        result.append(Experience(
            title=item.get("title") or item.get("role"),
            company=item.get("company") or item.get("organization"),
            location=item.get("location"),
            start_date=item.get("start_date") or item.get("from"),
            end_date=item.get("end_date") or item.get("to"),
            is_current=item.get("is_current") or item.get("currently_working"),
            duration_months=_safe_int(item.get("duration_months")),
            description=item.get("description") or item.get("responsibilities"),
            industry=item.get("industry"),
        ))
    return result


def _parse_education(raw_list: list) -> list[Education]:
    if not isinstance(raw_list, list):
        return []
    result = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        result.append(Education(
            degree=item.get("degree"),
            field_of_study=item.get("field_of_study") or item.get("major"),
            institution=item.get("institution") or item.get("school") or item.get("college"),
            start_year=_safe_int(item.get("start_year")),
            end_year=_safe_int(item.get("end_year") or item.get("graduation_year")),
            grade=item.get("grade") or item.get("gpa") or item.get("cgpa"),
        ))
    return result


def _parse_skills(raw: dict) -> Skills:
    skills_raw = raw.get("skills", {})
    if isinstance(skills_raw, list):
        all_skills = [s for s in skills_raw if isinstance(s, str)]
        return Skills(primary=all_skills, secondary=[], all_skills=all_skills)
    if isinstance(skills_raw, dict):
        primary = skills_raw.get("primary", []) or []
        secondary = skills_raw.get("secondary", []) or []
        all_skills = list(set(primary + secondary))
        return Skills(
            primary=[s for s in primary if isinstance(s, str)],
            secondary=[s for s in secondary if isinstance(s, str)],
            all_skills=[s for s in all_skills if isinstance(s, str)],
        )
    return Skills()


def _parse_certifications(raw_list: list) -> list[Certification]:
    if not isinstance(raw_list, list):
        return []
    result = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        result.append(Certification(
            name=item.get("name") or item.get("title"),
            issuer=item.get("issuer") or item.get("organization"),
            issue_date=item.get("issue_date") or item.get("date"),
            expiry_date=item.get("expiry_date"),
        ))
    return result


def _parse_languages(raw_list: list) -> list[Language]:
    if not isinstance(raw_list, list):
        return []
    result = []
    for item in raw_list:
        if isinstance(item, str):
            result.append(Language(name=item))
        elif isinstance(item, dict):
            result.append(Language(
                name=item.get("name") or item.get("language"),
                proficiency=item.get("proficiency") or item.get("level"),
            ))
    return result


def _parse_redrob_signals(raw: dict) -> RedrobSignals:
    signals = raw.get("redrob", {}) or raw.get("platform_signals", {}) or {}
    return RedrobSignals(
        profile_score=_safe_float(signals.get("profile_score") or raw.get("profile_score")),
        is_open_to_work=signals.get("is_open_to_work") or raw.get("open_to_work"),
        notice_period_days=_safe_int(signals.get("notice_period_days") or raw.get("notice_period")),
        last_active_days=_safe_int(signals.get("last_active_days")),
        application_count=_safe_int(signals.get("application_count")),
        response_rate=_safe_float(signals.get("response_rate")),
        has_github=bool(raw.get("github_url") or signals.get("github_url")),
        has_portfolio=bool(raw.get("portfolio_url") or signals.get("portfolio_url")),
        github_url=raw.get("github_url") or signals.get("github_url"),
        portfolio_url=raw.get("portfolio_url") or signals.get("portfolio_url"),
        linkedin_url=raw.get("linkedin_url") or signals.get("linkedin_url"),
    )


def _safe_float(value) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def _safe_int(value) -> Optional[int]:
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def parse_candidate(raw: dict) -> Optional[Candidate]:
    """Convert a raw JSON dict into a typed Candidate object."""
    if not isinstance(raw, dict):
        logger.warning("parse_candidate received non-dict input: %s", type(raw))
        return None
    try:
        candidate = Candidate(
            profile=_parse_profile(raw),
            experience=_parse_experience(raw.get("experience", [])),
            education=_parse_education(raw.get("education", [])),
            skills=_parse_skills(raw),
            certifications=_parse_certifications(raw.get("certifications", [])),
            languages=_parse_languages(raw.get("languages", [])),
            redrob=_parse_redrob_signals(raw),
        )
        candidate._raw = raw
        return candidate
    except ValidationError as e:
        logger.warning("Pydantic validation error: %s", e)
        return None
    except Exception as e:
        logger.error("Unexpected error parsing candidate: %s", e)
        return None


def parse_candidates(raw_records: list[dict]) -> list[Candidate]:
    """Parse a list of raw dicts into Candidate objects."""
    results = []
    for raw in raw_records:
        candidate = parse_candidate(raw)
        if candidate is not None:
            results.append(candidate)
    logger.info("Parsed %d candidates from %d records", len(results), len(raw_records))
    return results
