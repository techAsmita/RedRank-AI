"""
resolver.py
------------
Conflict Resolution Engine.

Handles specific contradictions between policy outcomes
that a weighted average would silently get wrong.

Every conflict rule is:
- Named
- Traceable to a JD signal
- Deterministic
- Applied in a fixed order

Rules are applied after tier assignment and before
final fusion score computation.
"""

from __future__ import annotations

from src.decision.models import PolicyResult, PolicyStatus
from src.features.intelligence_models import CandidateIntelligence
from src.fusion.models import (
    ConflictResolution,
    TIER_1,
    TIER_2,
    TIER_3,
    TIER_GATE,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find(results: list, name: str) -> PolicyResult:
    for r in results:
        if name.lower() in r.policy_name.lower():
            return r
    return None


def _status(result: PolicyResult) -> PolicyStatus:
    if result is None:
        return PolicyStatus.FAIL
    return result.status


def _confidence(result: PolicyResult) -> float:
    if result is None:
        return 0.0
    return result.confidence or 0.0


def _demote_tier(tier: str) -> str:
    """Demote a tier by exactly one level."""
    if tier == TIER_1:
        return TIER_2
    if tier == TIER_2:
        return TIER_3
    return TIER_3


# ── Conflict rules ────────────────────────────────────────────────────────────

def _conflict_technical_pass_hiring_fail(
    results: list,
    tier: str,
) -> tuple:
    """
    Conflict 1: Technically excellent but hiring-unavailable.

    Example: Strong production AI, 5y experience, 180-day notice,
             inactive, 5% response rate.

    Resolution: Demote one tier.
    Rationale: JD says these candidates are 'still in scope but
               the bar gets higher' — they compete, but not at the
               top of the list.

    Trigger: Technical Fit PASS AND Hiring Readiness FAIL
    """
    tech = _find(results, "Technical Fit")
    hiring = _find(results, "Hiring Readiness")

    if (
        _status(tech) == PolicyStatus.PASS
        and _status(hiring) == PolicyStatus.FAIL
    ):
        new_tier = _demote_tier(tier)
        return ConflictResolution(
            conflict_type="TECH_PASS_HIRING_FAIL",
            description="Strong technical fit undermined by hiring unavailability.",
            action_taken=f"Tier demoted from {tier} to {new_tier}.",
            tier_adjustment=-1,
            confidence_adjustment=0.0,
        ), new_tier

    return None, tier


def _conflict_high_risk_strong_technical(
    results: list,
    tier: str,
    booster_total: float,
) -> tuple:
    """
    Conflict 2: Strong technical fit but risk flags present.

    Example: Senior trajectory, excellent retrieval experience,
             but job-hopping flag + skill inflation.

    Resolution: Apply 15% confidence penalty to booster score.
    Rationale: Risk flags reduce confidence in the evidence
               quality, but don't eliminate the candidate.
               One flag is not a disqualifier; it's a caution.

    Trigger: Risk Assessment FAIL AND Technical Fit PASS/PARTIAL
    """
    risk = _find(results, "Risk Assessment")
    tech = _find(results, "Technical Fit")

    if (
        _status(risk) == PolicyStatus.FAIL
        and _status(tech) in (PolicyStatus.PASS, PolicyStatus.PARTIAL)
    ):
        penalty = round(booster_total * 0.15, 3)
        return ConflictResolution(
            conflict_type="HIGH_RISK_STRONG_TECH",
            description="Risk flags detected despite strong technical profile.",
            action_taken=f"Booster score reduced by 15% ({penalty:.3f} penalty).",
            tier_adjustment=0,
            confidence_adjustment=-penalty,
        ), booster_total - penalty

    return None, booster_total


def _conflict_strong_evidence_weak_domain(
    results: list,
    tier: str,
    intel: CandidateIntelligence,
) -> tuple:
    """
    Conflict 3: Highly complete profile but weak domain fit.

    Example: Perfect profile completeness, great GitHub presence,
             but primary skills are computer vision / robotics
             with no NLP/IR evidence.

    Resolution: Evidence Strength booster capped at 0.10
                (reduced to a minor signal, not a compensator).
    Rationale: Profile quality cannot compensate for domain mismatch.
               JD: 'CV/speech/robotics specialists without NLP/IR
               exposure — you'd be re-learning fundamentals here.'

    Trigger: Evidence Strength PASS AND
             Technical Fit FAIL AND
             JD Intent Coverage < 0.40
    """
    evidence = _find(results, "Evidence Strength")
    tech = _find(results, "Technical Fit")
    intent = _find(results, "JD Intent Coverage")

    if (
        _status(evidence) == PolicyStatus.PASS
        and _status(tech) == PolicyStatus.FAIL
        and _confidence(intent) < 0.40
    ):
        return ConflictResolution(
            conflict_type="STRONG_EVIDENCE_WEAK_DOMAIN",
            description="Strong profile evidence but wrong domain for the role.",
            action_taken="Evidence Strength booster contribution capped at 0.10.",
            tier_adjustment=0,
            confidence_adjustment=0.0,
        )

    return None


def _conflict_career_pass_intent_fail(
    results: list,
    tier: str,
) -> tuple:
    """
    Conflict 4: Good career trajectory but low JD intent coverage.

    Example: 8y experience, stable career, strong seniority,
             but skills/experience don't map to retrieval/ranking/LLM.

    Resolution: Demote one tier.
    Rationale: Career trajectory is necessary but not sufficient.
               A great career in the wrong domain doesn't satisfy
               the recruiter's intent.

    Trigger: Career Trajectory PASS AND JD Intent Coverage FAIL
    """
    career = _find(results, "Career Trajectory")
    intent = _find(results, "JD Intent Coverage")

    if (
        _status(career) == PolicyStatus.PASS
        and _status(intent) == PolicyStatus.FAIL
    ):
        new_tier = _demote_tier(tier)
        return ConflictResolution(
            conflict_type="CAREER_PASS_INTENT_FAIL",
            description="Strong career history but poor alignment with JD intent.",
            action_taken=f"Tier demoted from {tier} to {new_tier}.",
            tier_adjustment=-1,
            confidence_adjustment=0.0,
        ), new_tier

    return None, tier


def _conflict_production_pass_evidence_weak(
    results: list,
) -> tuple:
    """
    Conflict 5: Claims production experience but evidence is thin.

    Example: Says "built production ML systems" in description,
             but Evidence Strength is WEAK/FAIL, suggesting
             claims aren't backed by verifiable profile data.

    Resolution: Apply 10% penalty to tier score.
    Rationale: Weak evidence on a production claim is a signal
               that the claim may be unverifiable. We don't
               eliminate but we reduce confidence.

    Trigger: Production Readiness PASS AND Evidence Strength FAIL
    """
    prod = _find(results, "Production Readiness")
    evidence = _find(results, "Evidence Strength")

    if (
        _status(prod) == PolicyStatus.PASS
        and _status(evidence) == PolicyStatus.FAIL
    ):
        return ConflictResolution(
            conflict_type="PRODUCTION_PASS_EVIDENCE_WEAK",
            description="Production claims present but evidence quality is low.",
            action_taken="10% confidence penalty applied to tier score.",
            tier_adjustment=0,
            confidence_adjustment=-0.10,
        )

    return None


# ── Main resolver ─────────────────────────────────────────────────────────────

def resolve_conflicts(
    results: list,
    intel: CandidateIntelligence,
    tier: str,
    tier_score: float,
    booster_total: float,
) -> tuple:
    """
    Apply all conflict resolution rules in priority order.

    Returns:
        resolved_tier: str
        resolved_tier_score: float
        resolved_booster_total: float
        resolutions: List[ConflictResolution]
    """
    resolutions = []
    resolved_tier = tier
    resolved_tier_score = tier_score
    resolved_booster = booster_total

    # Rule 1: Technical PASS + Hiring FAIL → demote tier
    resolution, resolved_tier = _conflict_technical_pass_hiring_fail(
        results, resolved_tier
    )
    if resolution:
        resolutions.append(resolution)

    # Rule 2: High risk + strong tech → booster penalty
    resolution, resolved_booster = _conflict_high_risk_strong_technical(
        results, resolved_tier, resolved_booster
    )
    if resolution:
        resolutions.append(resolution)

    # Rule 3: Strong evidence + weak domain → (noted, handled in ranker)
    resolution = _conflict_strong_evidence_weak_domain(
        results, resolved_tier, intel
    )
    if resolution:
        resolutions.append(resolution)

    # Rule 4: Career PASS + Intent FAIL → demote tier
    resolution, resolved_tier = _conflict_career_pass_intent_fail(
        results, resolved_tier
    )
    if resolution:
        resolutions.append(resolution)

    # Rule 5: Production PASS + Evidence weak → tier score penalty
    resolution = _conflict_production_pass_evidence_weak(results)
    if resolution:
        resolved_tier_score = round(
            resolved_tier_score + resolution.confidence_adjustment, 3
        )
        resolved_tier_score = max(resolved_tier_score, 0.0)
        resolutions.append(resolution)

    return resolved_tier, resolved_tier_score, resolved_booster, resolutions
