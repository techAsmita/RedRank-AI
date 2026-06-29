from __future__ import annotations

from typing import Optional
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


class Education(BaseModel):
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    institution: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    grade: Optional[str] = None


class Certification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None


class Language(BaseModel):
    name: Optional[str] = None
    proficiency: Optional[str] = None


class Skills(BaseModel):
    primary: list[str] = Field(default_factory=list)
    secondary: list[str] = Field(default_factory=list)
    all_skills: list[str] = Field(default_factory=list)


class RedrobSignals(BaseModel):
    profile_score: Optional[float] = None
    is_open_to_work: Optional[bool] = None
    notice_period_days: Optional[int] = None
    last_active_days: Optional[int] = None
    application_count: Optional[int] = None
    response_rate: Optional[float] = None
    has_github: Optional[bool] = None
    has_portfolio: Optional[bool] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    linkedin_url: Optional[str] = None


class CandidateProfile(BaseModel):
    candidate_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    summary: Optional[str] = None
    years_of_experience: Optional[float] = None


class Candidate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    profile: CandidateProfile = Field(default_factory=CandidateProfile)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    certifications: list[Certification] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    redrob: RedrobSignals = Field(default_factory=RedrobSignals)

    _raw: dict = {}
