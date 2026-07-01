from __future__ import annotations

import logging
from typing import Optional

from src.features.intelligence_models import CandidateIntelligence
from src.job_intelligence.models import JobIntent
from src.evidence.models import (
    EvidenceGraph,
    EvidenceNode,
    EvidenceSource,
    STRONG, MODERATE, WEAK, NONE,
)

logger = logging.getLogger(__name__)


# ── Skill sets for evidence matching ─────────────────────────────────────────

PYTHON_SKILLS = {
    "python", "fastapi", "flask", "django",
    "numpy", "pandas", "pydantic",
}

RETRIEVAL_SKILLS = {
    "rag", "retrieval", "faiss", "pinecone", "chromadb",
    "weaviate", "milvus", "elasticsearch", "bm25", "opensearch",
}

EVALUATION_SKILLS = {
    "ragas", "evaluation", "evaluating", "benchmark", "ndcg",
    "mrr", "a/b testing", "ab testing", "model evaluation",
}

MLOPS_SKILLS = {
    "mlflow", "kubeflow", "airflow", "docker",
    "kubernetes", "wandb", "bentoml",
}

CLOUD_SKILLS = {
    "aws", "gcp", "azure", "google cloud", "amazon web services",
}

VECTOR_DB_SKILLS = {
    "faiss", "pinecone", "chromadb", "weaviate",
    "milvus", "qdrant", "pgvector",
}

RANKING_SKILLS = {
    "ranking", "reranking", "recommendation", "ltr",
    "learning to rank", "recommender", "bm25",
}

PRODUCTION_KEYWORDS = {
    "production", "deployed", "serving", "inference",
    "real-time", "latency", "scaled", "million users",
}


# ── Confidence mapping ────────────────────────────────────────────────────────

def _confidence(strength: float) -> str:
    if strength >= 0.75:
        return STRONG
    if strength >= 0.45:
        return MODERATE
    if strength > 0.0:
        return WEAK
    return NONE


# ── Core evidence builder ─────────────────────────────────────────────────────

def _build_skill_evidence(
    requirement: str,
    candidate_skills: list,
    target_skills: set,
    experience_months: int = 0,
    has_in_description: bool = False,
    has_certification: bool = False,
) -> EvidenceNode:
    """
    Build an EvidenceNode for a skill-based requirement.

    Strength is computed from multiple sources:
    - Skill present in profile         +0.30
    - Matching skill count bonus        up to +0.20
    - Evidence in job descriptions      +0.25
    - Experience duration               up to +0.15
    - Certification                     +0.10
    """
    node = EvidenceNode(requirement=requirement)
    sources = []
    strength = 0.0

    # Skills match
    skill_set = set(s.lower() for s in candidate_skills)
    matched = skill_set & target_skills

    if matched:
        strength += 0.30
        match_bonus = min(len(matched) / max(len(target_skills), 1), 1.0) * 0.20
        strength += match_bonus
        for skill in sorted(matched):
            sources.append(EvidenceSource(
                source_type="skill",
                value=skill,
            ))

    # Experience description evidence
    if has_in_description:
        strength += 0.25
        sources.append(EvidenceSource(
            source_type="experience",
            value="mentioned in job descriptions",
        ))

    # Duration bonus (up to 0.15 for 24+ months)
    if experience_months > 0:
        duration_bonus = min(experience_months / 24, 1.0) * 0.15
        strength += duration_bonus
        sources.append(EvidenceSource(
            source_type="experience",
            value=f"{experience_months} months",
            months=experience_months,
        ))

    # Certification bonus
    if has_certification:
        strength += 0.10
        sources.append(EvidenceSource(
            source_type="certification",
            value="certified",
        ))

    strength = min(round(strength, 3), 1.0)
    node.satisfied = strength > 0.0
    node.strength = strength
    node.confidence = _confidence(strength)
    node.sources = sources
    node.notes = (
        f"Matched {len(matched)} of {len(target_skills)} target skills"
        if matched else "No direct skill evidence found"
    )

    return node


# ── Individual evidence extractors ────────────────────────────────────────────

def _evidence_python(intel: CandidateIntelligence) -> EvidenceNode:
    skills = intel.technical.all_skills
    candidate_skills = intel.technical.python_adjacent_skills + (
        ["python"] if intel.technical.python_depth > 0 else []
    )
    return _build_skill_evidence(
        requirement="Python",
        candidate_skills=candidate_skills,
        target_skills=PYTHON_SKILLS,
        experience_months=int(intel.career.total_experience_years * 12),
        has_in_description=intel.technical.python_depth > 0,
    )


def _evidence_retrieval(intel: CandidateIntelligence) -> EvidenceNode:
    all_skills = intel.technical.all_skills
    return _build_skill_evidence(
        requirement="Retrieval",
        candidate_skills=all_skills,
        target_skills=RETRIEVAL_SKILLS,
        has_in_description=intel.technical.has_retrieval,
        experience_months=int(intel.career.ai_experience_years * 12),
    )


def _evidence_evaluation(intel: CandidateIntelligence) -> EvidenceNode:
    all_skills = intel.technical.all_skills
    return _build_skill_evidence(
        requirement="Evaluation",
        candidate_skills=all_skills,
        target_skills=EVALUATION_SKILLS,
        has_in_description=intel.technical.has_evaluation,
    )


def _evidence_mlops(intel: CandidateIntelligence) -> EvidenceNode:
    all_skills = intel.technical.all_skills
    return _build_skill_evidence(
        requirement="MLOps",
        candidate_skills=all_skills,
        target_skills=MLOPS_SKILLS,
        has_in_description=intel.technical.has_mlops,
    )


def _evidence_cloud(intel: CandidateIntelligence) -> EvidenceNode:
    all_skills = intel.technical.all_skills
    return _build_skill_evidence(
        requirement="Cloud",
        candidate_skills=all_skills,
        target_skills=CLOUD_SKILLS,
        has_in_description=intel.technical.cloud_platforms > 0,
    )


def _evidence_vector_db(intel: CandidateIntelligence) -> EvidenceNode:
    all_skills = intel.technical.all_skills
    return _build_skill_evidence(
        requirement="Vector DB",
        candidate_skills=all_skills,
        target_skills=VECTOR_DB_SKILLS,
        has_in_description=intel.technical.has_vector_db,
    )


def _evidence_ranking(intel: CandidateIntelligence) -> EvidenceNode:
    all_skills = intel.technical.all_skills
    return _build_skill_evidence(
        requirement="Ranking",
        candidate_skills=all_skills,
        target_skills=RANKING_SKILLS,
        has_in_description=intel.technical.has_ranking,
    )


def _evidence_production_ai(intel: CandidateIntelligence) -> EvidenceNode:
    node = EvidenceNode(requirement="Production AI")
    sources = []
    strength = 0.0

    if intel.technical.has_production_ai:
        strength += 0.50
        sources.append(EvidenceSource(
            source_type="experience",
            value="production AI evidence in job descriptions",
        ))

    if intel.career.ai_experience_years >= 2:
        strength += 0.30
        sources.append(EvidenceSource(
            source_type="experience",
            value=f"{intel.career.ai_experience_years} years AI experience",
            months=int(intel.career.ai_experience_years * 12),
        ))

    if intel.technical.has_mlops:
        strength += 0.20
        sources.append(EvidenceSource(
            source_type="skill",
            value="MLOps stack present",
        ))

    strength = min(round(strength, 3), 1.0)
    node.satisfied = strength > 0.0
    node.strength = strength
    node.confidence = _confidence(strength)
    node.sources = sources
    node.notes = "Production AI deployment evidence" if strength > 0 else "No production AI evidence"
    return node


def _evidence_experience_years(
    intel: CandidateIntelligence,
    required_years: Optional[float],
) -> EvidenceNode:
    node = EvidenceNode(requirement="Experience Years")
    actual = intel.career.total_experience_years
    required = required_years or 0

    sources = [EvidenceSource(
        source_type="experience",
        value=f"{actual} years total experience",
        months=int(actual * 12),
    )]

    if required == 0:
        strength = 0.5
    elif actual >= required:
        strength = min(actual / required, 1.5) / 1.5
    else:
        strength = actual / required * 0.6

    strength = min(round(strength, 3), 1.0)
    node.satisfied = actual >= required if required > 0 else True
    node.strength = strength
    node.confidence = _confidence(strength)
    node.sources = sources
    node.notes = f"{actual}y actual vs {required}y required"
    return node


def _evidence_seniority(intel: CandidateIntelligence) -> EvidenceNode:
    node = EvidenceNode(requirement="Seniority")
    level = intel.career.seniority_level or "unknown"

    SENIORITY_STRENGTH = {
        "principal": 1.0, "executive": 1.0,
        "senior": 0.85, "lead": 0.85,
        "mid": 0.60,
        "junior": 0.30,
        "intern": 0.10,
        "unknown": 0.20,
    }

    strength = SENIORITY_STRENGTH.get(level, 0.20)
    node.satisfied = strength >= 0.6
    node.strength = strength
    node.confidence = _confidence(strength)
    node.sources = [EvidenceSource(source_type="experience", value=level)]
    node.notes = f"Seniority level: {level}"
    return node


def _evidence_career_growth(intel: CandidateIntelligence) -> EvidenceNode:
    node = EvidenceNode(requirement="Career Growth")
    rate = intel.career.career_growth_rate

    if rate > 0.5:
        strength = 1.0
        note = "Strong upward trajectory"
    elif rate > 0:
        strength = 0.65
        note = "Positive growth"
    elif rate == 0:
        strength = 0.40
        note = "Lateral movement"
    else:
        strength = 0.20
        note = "Declining trajectory"

    node.satisfied = strength >= 0.5
    node.strength = round(strength, 3)
    node.confidence = _confidence(strength)
    node.sources = [EvidenceSource(
        source_type="experience",
        value=f"growth rate {rate} per year",
    )]
    node.notes = note
    return node


def _evidence_ai_experience(intel: CandidateIntelligence) -> EvidenceNode:
    node = EvidenceNode(requirement="AI Experience")
    years = intel.career.ai_experience_years

    strength = min(years / 5.0, 1.0)
    node.satisfied = years > 0
    node.strength = round(strength, 3)
    node.confidence = _confidence(strength)
    node.sources = [EvidenceSource(
        source_type="experience",
        value=f"{years} years in AI/ML roles",
        months=int(years * 12),
    )]
    node.notes = f"{years} years of direct AI experience"
    return node


def _evidence_education(intel: CandidateIntelligence) -> EvidenceNode:
    node = EvidenceNode(requirement="Education")
    sources = []

    tier = intel.education.degree_tier
    strength = tier / 5.0

    if intel.education.highest_degree:
        sources.append(EvidenceSource(
            source_type="education",
            value=intel.education.highest_degree,
        ))
    if intel.education.is_elite_institution:
        strength = min(strength + 0.20, 1.0)
        sources.append(EvidenceSource(
            source_type="education",
            value="elite institution",
        ))
    if intel.education.is_stem:
        strength = min(strength + 0.10, 1.0)
        sources.append(EvidenceSource(
            source_type="education",
            value="STEM field",
        ))
    if intel.education.education_ai_focus:
        strength = min(strength + 0.10, 1.0)
        sources.append(EvidenceSource(
            source_type="education",
            value="AI/ML focus",
        ))

    strength = round(strength, 3)
    node.satisfied = tier >= 3
    node.strength = strength
    node.confidence = _confidence(strength)
    node.sources = sources
    node.notes = f"Degree tier {tier}/5"
    return node


def _evidence_github(intel: CandidateIntelligence) -> EvidenceNode:
    node = EvidenceNode(requirement="GitHub Presence")
    strength = 0.0
    sources = []

    if intel.behavior.has_github:
        strength += 0.70
        sources.append(EvidenceSource(source_type="behavior", value="GitHub profile present"))
    if intel.behavior.has_portfolio:
        strength += 0.30
        sources.append(EvidenceSource(source_type="behavior", value="Portfolio present"))

    strength = min(round(strength, 3), 1.0)
    node.satisfied = intel.behavior.has_github
    node.strength = strength
    node.confidence = _confidence(strength)
    node.sources = sources
    node.notes = "Public work evidence" if strength > 0 else "No public work found"
    return node


def _evidence_certifications(intel: CandidateIntelligence) -> EvidenceNode:
    node = EvidenceNode(requirement="Certifications")
    sources = []
    strength = 0.0

    if intel.behavior.has_ai_certifications:
        strength += 0.60
        for name in intel.behavior.ai_certification_names:
            sources.append(EvidenceSource(source_type="certification", value=name))

    count_bonus = min(intel.behavior.certification_count / 5, 1.0) * 0.40
    strength = min(round(strength + count_bonus, 3), 1.0)

    node.satisfied = intel.behavior.certification_count > 0
    node.strength = strength
    node.confidence = _confidence(strength)
    node.sources = sources
    node.notes = f"{intel.behavior.certification_count} certifications"
    return node


def _evidence_availability(intel: CandidateIntelligence) -> EvidenceNode:
    node = EvidenceNode(requirement="Availability")
    sources = []
    strength = 0.5

    if intel.behavior.is_open_to_work:
        strength += 0.30
        sources.append(EvidenceSource(source_type="behavior", value="open to work"))

    notice = intel.behavior.notice_period_days
    if notice is not None:
        if notice == 0:
            strength += 0.20
            sources.append(EvidenceSource(source_type="behavior", value="immediate joiner"))
        elif notice <= 30:
            strength += 0.15
            sources.append(EvidenceSource(source_type="behavior", value=f"{notice}d notice"))
        elif notice <= 60:
            strength += 0.05
            sources.append(EvidenceSource(source_type="behavior", value=f"{notice}d notice"))
        else:
            strength -= 0.10
            sources.append(EvidenceSource(source_type="behavior", value=f"{notice}d notice (long)"))

    strength = min(max(round(strength, 3), 0.0), 1.0)
    node.satisfied = True
    node.strength = strength
    node.confidence = _confidence(strength)
    node.sources = sources
    node.notes = f"Notice: {notice}d, Open: {intel.behavior.is_open_to_work}"
    return node


def _evidence_profile_quality(intel: CandidateIntelligence) -> EvidenceNode:
    node = EvidenceNode(requirement="Profile Quality")
    completeness = intel.behavior.profile_completeness

    node.satisfied = completeness >= 0.7
    node.strength = round(completeness, 3)
    node.confidence = _confidence(completeness)
    node.sources = [EvidenceSource(
        source_type="behavior",
        value=f"{int(completeness * 100)}% complete",
    )]
    node.notes = f"Profile completeness: {int(completeness * 100)}%"
    return node


def _evidence_risk(intel: CandidateIntelligence) -> EvidenceNode:
    node = EvidenceNode(requirement="Risk Flags")
    risk = intel.risk
    sources = []

    if risk.has_timeline_gaps:
        sources.append(EvidenceSource(source_type="risk", value=f"gap {risk.timeline_gap_months}m"))
    if risk.job_hopping_flag:
        sources.append(EvidenceSource(source_type="risk", value="job hopping"))
    if risk.skill_inflation_flag:
        sources.append(EvidenceSource(source_type="risk", value="skill inflation"))
    if risk.suspicious_skill_count:
        sources.append(EvidenceSource(source_type="risk", value="suspicious skill count"))

    # Invert: fewer flags = higher strength (less risky)
    strength = max(0.0, 1.0 - (risk.risk_flag_count * 0.20))
    strength = round(strength, 3)

    node.satisfied = risk.risk_flag_count == 0
    node.strength = strength
    node.confidence = _confidence(strength)
    node.sources = sources
    node.notes = f"{risk.risk_flag_count} risk flags"
    return node


# ── Main builder ──────────────────────────────────────────────────────────────

def build_evidence_graph(
    intel: CandidateIntelligence,
    job_intent: JobIntent,
) -> EvidenceGraph:
    """
    Build a complete EvidenceGraph for one candidate against one JD.

    Every node is evidence-backed.
    No scores are computed here.
    """
    graph = EvidenceGraph(
        candidate_id=intel.candidate_id,
        candidate_name=intel.name,
        job_title=job_intent.metadata.title,
    )

    # Technical
    graph.python         = _evidence_python(intel)
    graph.retrieval      = _evidence_retrieval(intel)
    graph.evaluation     = _evidence_evaluation(intel)
    graph.mlops          = _evidence_mlops(intel)
    graph.cloud          = _evidence_cloud(intel)
    graph.production_ai  = _evidence_production_ai(intel)
    graph.vector_db      = _evidence_vector_db(intel)
    graph.ranking        = _evidence_ranking(intel)

    # Career
    graph.experience_years = _evidence_experience_years(
        intel, job_intent.technical.minimum_years
    )
    graph.seniority      = _evidence_seniority(intel)
    graph.career_growth  = _evidence_career_growth(intel)
    graph.ai_experience  = _evidence_ai_experience(intel)

    # Education
    graph.education      = _evidence_education(intel)

    # Behavior
    graph.github_presence  = _evidence_github(intel)
    graph.certifications   = _evidence_certifications(intel)
    graph.availability     = _evidence_availability(intel)
    graph.profile_quality  = _evidence_profile_quality(intel)

    # Risk
    graph.risk_flags     = _evidence_risk(intel)

    return graph


def build_evidence_batch(
    intelligence_list: list,
    job_intent: JobIntent,
) -> list:
    """Build evidence graphs for all candidates."""
    results = []
    for intel in intelligence_list:
        try:
            graph = build_evidence_graph(intel, job_intent)
            results.append(graph)
        except Exception as e:
            logger.error("Evidence graph failed for %s: %s", intel.candidate_id, e)
    logger.info("Evidence graphs built: %d", len(results))
    return results
