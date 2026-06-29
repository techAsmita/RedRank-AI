"""
models.py
---------

Structured representation of recruiter intent extracted from a job description.

These models intentionally contain NO parsing logic.

Responsibilities:
- Represent recruiter intent
- Store structured requirements
- Provide safe defaults
- Remain independent of parsing, evidence and ranking
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------

@dataclass
class JobMetadata:
    """Basic metadata about the job posting."""

    company: str | None = None
    department: str | None = None
    title: str | None = None
    employment_type: str | None = None
    location: str | None = None
    source_file: str | None = None


# ---------------------------------------------------------------------
# Technical
# ---------------------------------------------------------------------

@dataclass
class TechnicalRequirements:
    """Technical capabilities expected by the recruiter."""

    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)

    skill_categories: list[str] = field(default_factory=list)

    minimum_years: float | None = None

    production_ai: bool = False
    retrieval: bool = False
    ranking: bool = False
    evaluation: bool = False
    mlops: bool = False

    python_required: bool = False
    cloud_required: bool = False
    distributed_systems: bool = False
    leadership_required: bool = False


# ---------------------------------------------------------------------
# Career
# ---------------------------------------------------------------------

@dataclass
class CareerRequirements:
    """Career expectations."""

    minimum_experience_years: float | None = None
    preferred_experience_years: float | None = None

    acceptable_titles: list[str] = field(default_factory=list)

    seniority: str | None = None

    startup_background: bool = False
    enterprise_background: bool = False
    research_background: bool = False
    management_background: bool = False


# ---------------------------------------------------------------------
# Behaviour
# ---------------------------------------------------------------------

@dataclass
class BehaviorRequirements:
    """Behavioral signals recruiters care about."""

    ownership: bool = False
    product_mindset: bool = False
    communication: bool = False
    mentorship: bool = False
    cross_functional: bool = False
    customer_focus: bool = False
    problem_solving: bool = False
    learning_mindset: bool = False
    ambiguity_tolerance: bool = False


# ---------------------------------------------------------------------
# Hiring Preferences
# ---------------------------------------------------------------------

@dataclass
class HiringPreferences:
    """Recruiter preferences that are not strict requirements."""

    locations: list[str] = field(default_factory=list)

    remote: bool = False
    hybrid: bool = False
    onsite: bool = False

    preferred_companies: list[str] = field(default_factory=list)
    preferred_degrees: list[str] = field(default_factory=list)
    preferred_domains: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------
# Disqualifiers
# ---------------------------------------------------------------------

@dataclass
class Disqualifiers:
    """Explicit hard requirements."""

    requires_authorization: bool = False
    mandatory_degree: bool = False
    mandatory_python: bool = False
    mandatory_production_ai: bool = False
    mandatory_retrieval: bool = False

    other: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------
# Scoring Preferences
# ---------------------------------------------------------------------

@dataclass
class ScoringPreferences:
    """
    Priority hints extracted from the JD.

    No scores are computed here.
    """

    must_have: list[str] = field(default_factory=list)
    nice_to_have: list[str] = field(default_factory=list)

    priority_skills: list[str] = field(default_factory=list)
    priority_behaviors: list[str] = field(default_factory=list)
    priority_experience: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------
# Root Intent
# ---------------------------------------------------------------------

@dataclass
class JobIntent:
    """
    Structured recruiter intent.

    This becomes the single source of truth for everything the recruiter
    is actually looking for.

    No ranking information is stored here.
    """

    metadata: JobMetadata = field(default_factory=JobMetadata)

    technical: TechnicalRequirements = field(
        default_factory=TechnicalRequirements
    )

    career: CareerRequirements = field(
        default_factory=CareerRequirements
    )

    behavior: BehaviorRequirements = field(
        default_factory=BehaviorRequirements
    )

    hiring: HiringPreferences = field(
        default_factory=HiringPreferences
    )

    disqualifiers: Disqualifiers = field(
        default_factory=Disqualifiers
    )

    scoring: ScoringPreferences = field(
        default_factory=ScoringPreferences
    )

    raw_text: str = ""