from __future__ import annotations

from typing import Optional, Dict
from pydantic import BaseModel, Field, ConfigDict


class Experience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: Optional[bool] = None
    duration_months: Optional[int] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None


class Education(BaseModel):
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    institution: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    grade: Optional[str] = None
    tier: Optional[str] = None


class Certification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    year: Optional[int] = None


class Language(BaseModel):
    name: Optional[str] = None
    proficiency: Optional[str] = None


class SkillEntry(BaseModel):
    """
    A single skill with rich evidence attached.

    Real schema gives us proficiency, endorsements, and duration per skill —
    far richer than a flat skill name. We preserve all of it.
    """
    name: str
    proficiency: Optional[str] = None
    endorsements: int = 0
    duration_months: int = 0


class SalaryRange(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None


class RedrobSignals(BaseModel):
    """
    Platform-specific signals from Redrob's dataset.
    Maps directly to the real `redrob_signals` schema.
    """
    profile_completeness_score: Optional[float] = None
    signup_date: Optional[str] = None
    last_active_date: Optional[str] = None
    open_to_work_flag: Optional[bool] = None
    profile_views_received_30d: Optional[int] = None
    applications_submitted_30d: Optional[int] = None
    recruiter_response_rate: Optional[float] = None
    avg_response_time_hours: Optional[float] = None
    skill_assessment_scores: Dict[str, float] = Field(default_factory=dict)
    connection_count: Optional[int] = None
    endorsements_received: Optional[int] = None
    notice_period_days: Optional[int] = None
    expected_salary_range_inr_lpa: Optional[SalaryRange] = None
    preferred_work_mode: Optional[str] = None
    willing_to_relocate: Optional[bool] = None
    github_activity_score: Optional[float] = None
    search_appearance_30d: Optional[int] = None
    saved_by_recruiters_30d: Optional[int] = None
    interview_completion_rate: Optional[float] = None
    offer_acceptance_rate: Optional[float] = None
    verified_email: Optional[bool] = None
    verified_phone: Optional[bool] = None
    linkedin_connected: Optional[bool] = None


class CandidateProfile(BaseModel):
    candidate_id: Optional[str] = None
    name: Optional[str] = None
    headline: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    current_company_size: Optional[str] = None
    current_industry: Optional[str] = None
    summary: Optional[str] = None
    years_of_experience: Optional[float] = None


class Candidate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    profile: CandidateProfile = Field(default_factory=CandidateProfile)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[SkillEntry] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    redrob: RedrobSignals = Field(default_factory=RedrobSignals)

    _raw: dict = {}
