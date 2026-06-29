from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TechnicalIntelligence:
    """
    What the candidate can actually build.
    Every field derived from skills or experience descriptions.
    """
    python_depth: int = 0                    # Count of Python ecosystem skills
    ai_ml_depth: int = 0                     # Count of distinct AI/ML categories
    skill_count: int = 0                     # Total normalized skills
    skill_diversity: int = 0                 # Number of distinct skill categories
    cloud_platforms: int = 0                 # Count of cloud platforms known
    has_vector_db: bool = False              # Pinecone/Weaviate/ChromaDB/FAISS/Qdrant
    has_retrieval: bool = False              # RAG/search/elasticsearch/retrieval
    has_ranking: bool = False               # Ranking/reranking/LTR/recommendation
    has_evaluation: bool = False            # A/B testing/model eval/NDCG/metrics
    has_production_ai: bool = False         # Deployed ML evidence in descriptions
    has_mlops: bool = False                 # MLflow/Kubeflow/Airflow/Docker/K8s
    python_adjacent_skills: list = field(default_factory=list)   # Evidence list
    ai_skill_categories: list = field(default_factory=list)      # Evidence list


@dataclass
class CareerIntelligence:
    """
    How the candidate's career has progressed.
    Every field derived from experience history.
    """
    total_experience_years: float = 0.0
    ai_experience_years: float = 0.0
    number_of_companies: int = 0
    number_of_roles: int = 0
    average_tenure_months: float = 0.0
    longest_tenure_months: int = 0
    shortest_tenure_months: int = 0
    job_hopping_rate: float = 0.0           # Roles < 12 months / total roles
    career_growth_rate: float = 0.0         # Seniority delta per year
    company_diversity: int = 0              # Distinct industries
    startup_ratio: float = 0.0             # Non-enterprise roles / total roles
    is_currently_employed: bool = False
    days_since_last_role: Optional[int] = None
    current_title_normalized: Optional[str] = None
    current_company_normalized: Optional[str] = None
    seniority_level: Optional[str] = None   # junior/mid/senior/lead/principal
    title_progression: list = field(default_factory=list)  # Ordered title history


@dataclass
class EducationIntelligence:
    """
    Academic background signals.
    Every field derived from education records.
    """
    degree_tier: int = 0                    # 1-5 ordinal
    highest_degree: Optional[str] = None
    is_stem: bool = False
    is_elite_institution: bool = False
    has_postgrad: bool = False
    education_ai_focus: bool = False
    institutions: list = field(default_factory=list)
    fields_of_study: list = field(default_factory=list)


@dataclass
class BehaviorIntelligence:
    """
    Observable engagement and activity signals.
    Every field derived from redrob signals or profile metadata.
    """
    has_github: bool = False
    has_portfolio: bool = False
    has_linkedin: bool = False
    certification_count: int = 0
    has_ai_certifications: bool = False
    ai_certification_names: list = field(default_factory=list)
    multilingual: bool = False
    language_count: int = 0
    profile_completeness: float = 0.0
    is_open_to_work: bool = False
    notice_period_days: Optional[int] = None
    last_active_days: Optional[int] = None
    response_rate: Optional[float] = None


@dataclass
class RiskIntelligence:
    """
    Observable anomalies in the candidate profile.
    No classification — only flags with evidence.
    """
    has_timeline_gaps: bool = False
    timeline_gap_months: int = 0            # Largest gap in months
    has_timeline_overlap: bool = False
    overlap_count: int = 0
    job_hopping_flag: bool = False
    skill_inflation_flag: bool = False
    suspicious_skill_count: bool = False
    missing_dates_ratio: float = 0.0
    short_descriptions_ratio: float = 0.0
    risk_flag_count: int = 0               # Total number of flags triggered


@dataclass
class CandidateIntelligence:
    """
    Root intelligence object for a candidate.
    Aggregates all intelligence dimensions.
    Input to Phase 3 ranking engine.
    """
    candidate_id: Optional[str] = None
    name: Optional[str] = None

    technical: TechnicalIntelligence = field(default_factory=TechnicalIntelligence)
    career: CareerIntelligence = field(default_factory=CareerIntelligence)
    education: EducationIntelligence = field(default_factory=EducationIntelligence)
    behavior: BehaviorIntelligence = field(default_factory=BehaviorIntelligence)
    risk: RiskIntelligence = field(default_factory=RiskIntelligence)
