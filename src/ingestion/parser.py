from __future__ import annotations

"""
parser.py
---------
Converts raw JSON dicts (real Redrob schema) into typed Candidate objects.
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
    SalaryRange,
    SkillEntry,
)

logger = logging.getLogger(__name__)


def _parse_profile(raw: dict) -> CandidateProfile:
    p = raw.get("profile", {}) or {}
    return CandidateProfile(
        candidate_id=raw.get("candidate_id"),
        name=p.get("anonymized_name") or p.get("name"),
        headline=p.get("headline"),
        email=p.get("email"),
        phone=p.get("phone"),
        location=p.get("location"),
        country=p.get("country"),
        current_title=p.get("current_title"),
        current_company=p.get("current_company"),
        current_company_size=p.get("current_company_size"),
        current_industry=p.get("current_industry"),
        summary=p.get("summary"),
        years_of_experience=_safe_float(p.get("years_of_experience")),
    )


def _parse_experience(raw_list: list) -> list[Experience]:
    if not isinstance(raw_list, list):
        return []
    result = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        result.append(Experience(
            title=item.get("title"),
            company=item.get("company"),
            location=item.get("location"),
            start_date=item.get("start_date"),
            end_date=item.get("end_date"),
            is_current=item.get("is_current"),
            duration_months=_safe_int(item.get("duration_months")),
            description=item.get("description"),
            industry=item.get("industry"),
            company_size=item.get("company_size"),
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
            field_of_study=item.get("field_of_study"),
            institution=item.get("institution"),
            start_year=_safe_int(item.get("start_year")),
            end_year=_safe_int(item.get("end_year")),
            grade=item.get("grade"),
            tier=item.get("tier"),
        ))
    return result


def _parse_skills(raw_list: list) -> list[SkillEntry]:
    """
    Real schema: skills is a list of rich objects.
    {name, proficiency, endorsements, duration_months}
    """
    if not isinstance(raw_list, list):
        return []
    result = []
    for item in raw_list:
        if isinstance(item, str):
            # Fallback for older/sample schema (flat string list)
            result.append(SkillEntry(name=item))
        elif isinstance(item, dict) and item.get("name"):
            result.append(SkillEntry(
                name=item["name"],
                proficiency=item.get("proficiency"),
                endorsements=_safe_int(item.get("endorsements")) or 0,
                duration_months=_safe_int(item.get("duration_months")) or 0,
            ))
    return result


def _parse_certifications(raw_list: list) -> list[Certification]:
    if not isinstance(raw_list, list):
        return []
    result = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        result.append(Certification(
            name=item.get("name"),
            issuer=item.get("issuer"),
            year=_safe_int(item.get("year")),
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
                name=item.get("language") or item.get("name"),
                proficiency=item.get("proficiency"),
            ))
    return result


def _parse_redrob_signals(raw: dict) -> RedrobSignals:
    s = raw.get("redrob_signals", {}) or {}

    salary = None
    salary_raw = s.get("expected_salary_range_inr_lpa")
    if isinstance(salary_raw, dict):
        salary = SalaryRange(
            min=_safe_float(salary_raw.get("min")),
            max=_safe_float(salary_raw.get("max")),
        )

    return RedrobSignals(
        profile_completeness_score=_safe_float(s.get("profile_completeness_score")),
        signup_date=s.get("signup_date"),
        last_active_date=s.get("last_active_date"),
        open_to_work_flag=s.get("open_to_work_flag"),
        profile_views_received_30d=_safe_int(s.get("profile_views_received_30d")),
        applications_submitted_30d=_safe_int(s.get("applications_submitted_30d")),
        recruiter_response_rate=_safe_float(s.get("recruiter_response_rate")),
        avg_response_time_hours=_safe_float(s.get("avg_response_time_hours")),
        skill_assessment_scores=s.get("skill_assessment_scores") or {},
        connection_count=_safe_int(s.get("connection_count")),
        endorsements_received=_safe_int(s.get("endorsements_received")),
        notice_period_days=_safe_int(s.get("notice_period_days")),
        expected_salary_range_inr_lpa=salary,
        preferred_work_mode=s.get("preferred_work_mode"),
        willing_to_relocate=s.get("willing_to_relocate"),
        github_activity_score=_safe_float(s.get("github_activity_score")),
        search_appearance_30d=_safe_int(s.get("search_appearance_30d")),
        saved_by_recruiters_30d=_safe_int(s.get("saved_by_recruiters_30d")),
        interview_completion_rate=_safe_float(s.get("interview_completion_rate")),
        offer_acceptance_rate=_safe_float(s.get("offer_acceptance_rate")),
        verified_email=s.get("verified_email"),
        verified_phone=s.get("verified_phone"),
        linkedin_connected=s.get("linkedin_connected"),
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
    """Convert a raw JSON dict (real Redrob schema) into a typed Candidate object."""
    if not isinstance(raw, dict):
        logger.warning("parse_candidate received non-dict input: %s", type(raw))
        return None
    try:
        candidate = Candidate(
            profile=_parse_profile(raw),
            experience=_parse_experience(raw.get("career_history", [])),
            education=_parse_education(raw.get("education", [])),
            skills=_parse_skills(raw.get("skills", [])),
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
