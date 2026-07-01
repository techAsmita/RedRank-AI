"""
reasoning.py
-------------
Generates structured, recruiter-friendly reasoning for each
ranked candidate.

No LLM. No templates copied from documentation.
Every sentence is built deterministically from FusionScore,
PolicyResult, and CandidateIntelligence fields.

Output is designed to answer the recruiter's question:
"Why is this candidate ranked here?"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.decision.models import PolicyResult, PolicyStatus
from src.features.intelligence_models import CandidateIntelligence
from src.fusion.models import FusionScore, TIER_1, TIER_2, TIER_3, TIER_GATE


@dataclass
class CandidateReasoning:
    """Full structured reasoning for one ranked candidate."""
    candidate_id: Optional[str] = None
    candidate_name: Optional[str] = None
    rank: Optional[int] = None
    tier: Optional[str] = None
    fusion_score: float = 0.0

    # Structured sections
    headline: str = ""
    technical_summary: str = ""
    career_summary: str = ""
    availability_summary: str = ""
    risk_summary: str = ""
    conflict_summary: str = ""
    overall_verdict: str = ""

    # Evidence references
    key_strengths: list = field(default_factory=list)
    key_concerns: list = field(default_factory=list)


def _find(results: list, name: str) -> Optional[PolicyResult]:
    for r in results:
        if name.lower() in r.policy_name.lower():
            return r
    return None


def _confidence_label(confidence: float) -> str:
    if confidence >= 0.75:
        return "strong"
    if confidence >= 0.50:
        return "moderate"
    if confidence >= 0.30:
        return "weak"
    return "very weak"


def _tier_label(tier: str) -> str:
    return {
        TIER_1: "Tier 1 — Strong Match",
        TIER_2: "Tier 2 — Competitive",
        TIER_3: "Tier 3 — Weak Match",
        TIER_GATE: "Disqualified — Gate Failure",
    }.get(tier, tier)


def _build_headline(
    score: FusionScore,
    intel: CandidateIntelligence,
) -> str:
    name = intel.name or intel.candidate_id
    tier_label = _tier_label(score.tier)
    return (
        f"{name} | Rank #{score.rank} | {tier_label} | "
        f"Score {score.fusion_score:.4f}"
    )


def _build_technical_summary(
    results: list,
    intel: CandidateIntelligence,
) -> tuple:
    """Returns (summary_str, strengths, concerns)"""
    tech = _find(results, "Technical Fit")
    prod = _find(results, "Production Readiness")
    intent = _find(results, "JD Intent Coverage")

    strengths = []
    concerns = []
    parts = []

    if tech:
        label = _confidence_label(tech.confidence)
        parts.append(
            f"Technical fit is {label} ({tech.confidence:.2f})."
        )
        for e in tech.supporting_evidence[:2]:
            strengths.append(f"[Technical] {e.field}: {e.explanation}")
        for c in tech.concerns[:2]:
            concerns.append(f"[Technical] {c.field}: {c.explanation}")

    if prod:
        label = _confidence_label(prod.confidence)
        parts.append(
            f"Production readiness is {label} ({prod.confidence:.2f})."
        )
        if prod.status == PolicyStatus.FAIL:
            concerns.append(
                "[Production] No evidence of deployed production AI systems."
            )
        elif prod.supporting_evidence:
            strengths.append(
                f"[Production] {prod.supporting_evidence[0].explanation}"
            )

    if intent:
        label = _confidence_label(intent.confidence)
        parts.append(
            f"JD intent coverage is {label} ({intent.confidence:.2f})."
        )
        for c in intent.concerns[:1]:
            concerns.append(f"[Intent] {c.field}: {c.explanation}")

    if intel.technical.ai_skill_categories:
        parts.append(
            f"AI/ML skill categories present: "
            f"{', '.join(intel.technical.ai_skill_categories[:4])}."
        )

    return " ".join(parts), strengths, concerns


def _build_career_summary(
    results: list,
    intel: CandidateIntelligence,
) -> tuple:
    """Returns (summary_str, strengths, concerns)"""
    career = _find(results, "Career Trajectory")
    strengths = []
    concerns = []
    parts = []

    parts.append(
        f"{intel.career.total_experience_years:.1f} years total experience, "
        f"{intel.career.ai_experience_years:.1f} years in AI/ML roles."
    )

    if intel.career.seniority_level:
        parts.append(
            f"Seniority: {intel.career.seniority_level}."
        )

    if intel.career.job_hopping_flag:
        concerns.append(
            f"[Career] Job hopping detected "
            f"(rate={intel.career.job_hopping_rate:.2f})."
        )
    else:
        strengths.append("[Career] Stable tenure history.")

    if career:
        label = _confidence_label(career.confidence)
        parts.append(
            f"Career trajectory is {label} ({career.confidence:.2f})."
        )

    if intel.education.is_elite_institution:
        strengths.append(
            f"[Education] Elite institution: "
            f"{', '.join(intel.education.institutions[:2])}."
        )

    if intel.education.has_postgrad:
        strengths.append(
            f"[Education] {intel.education.highest_degree} — "
            f"postgraduate qualification."
        )

    return " ".join(parts), strengths, concerns


def _build_availability_summary(
    results: list,
    intel: CandidateIntelligence,
) -> tuple:
    """Returns (summary_str, strengths, concerns)"""
    hiring = _find(results, "Hiring Readiness")
    strengths = []
    concerns = []
    parts = []

    notice = intel.behavior.notice_period_days
    if notice is not None:
        if notice <= 30:
            parts.append(f"Notice period: {notice} days (immediate/fast joiner).")
            strengths.append(f"[Availability] {notice}-day notice period.")
        elif notice <= 60:
            parts.append(f"Notice period: {notice} days (standard).")
        else:
            parts.append(f"Notice period: {notice} days (long).")
            concerns.append(f"[Availability] {notice}-day notice may delay hire.")

    if intel.behavior.is_open_to_work:
        strengths.append("[Availability] Actively open to work.")
        parts.append("Actively open to new roles.")

    rr = intel.behavior.response_rate
    if rr is not None:
        if rr >= 0.70:
            strengths.append(f"[Engagement] High recruiter response rate ({rr:.0%}).")
        elif rr < 0.30:
            concerns.append(
                f"[Engagement] Low recruiter response rate ({rr:.0%}) "
                f"— engagement risk."
            )

    lad = intel.behavior.last_active_days
    if lad is not None:
        if lad <= 7:
            strengths.append(f"[Activity] Active within last {lad} day(s).")
        elif lad > 60:
            concerns.append(f"[Activity] Last active {lad} days ago.")

    return " ".join(parts) if parts else "Availability data unavailable.", \
           strengths, concerns


def _build_risk_summary(
    results: list,
    intel: CandidateIntelligence,
) -> tuple:
    """Returns (summary_str, strengths, concerns)"""
    risk_result = _find(results, "Risk Assessment")
    strengths = []
    concerns = []

    flag_count = intel.risk.risk_flag_count

    if flag_count == 0:
        summary = "No risk flags detected."
        strengths.append("[Risk] Clean profile — no anomalies detected.")
    else:
        flags = []
        if intel.risk.has_timeline_gaps:
            flags.append(f"timeline gap ({intel.risk.timeline_gap_months}mo)")
        if intel.risk.job_hopping_flag:
            flags.append("job hopping")
        if intel.risk.skill_inflation_flag:
            flags.append("skill inflation")
        if intel.risk.suspicious_skill_count:
            flags.append("suspicious skill count")
        summary = f"{flag_count} risk flag(s): {', '.join(flags)}."
        for f in flags:
            concerns.append(f"[Risk] {f.capitalize()} detected.")

    return summary, strengths, concerns


def _build_conflict_summary(score: FusionScore) -> str:
    if not score.conflicts_resolved:
        return "No conflicts requiring resolution."
    parts = []
    for c in score.conflicts_resolved:
        parts.append(f"{c.conflict_type}: {c.action_taken}")
    return " | ".join(parts)


def _build_overall_verdict(
    score: FusionScore,
    intel: CandidateIntelligence,
) -> str:
    name = intel.name or intel.candidate_id

    if score.tier == TIER_GATE:
        return (
            f"{name} did not pass hard eligibility gates and has been "
            f"deprioritized. Reason: {score.gate_result.notes}"
        )

    if score.tier == TIER_1:
        return (
            f"{name} is a strong match for this role. All anchor policies "
            f"indicate sufficient confidence, and booster signals further "
            f"support the recommendation."
        )

    if score.tier == TIER_2:
        weakest = min(score.anchor_scores, key=score.anchor_scores.get)
        return (
            f"{name} is a competitive candidate with mixed signals. "
            f"The limiting factor is {weakest} "
            f"({score.anchor_scores[weakest]:.2f} confidence). "
            f"Consider for shortlist with caveats."
        )

    return (
        f"{name} has significant gaps relative to this role's requirements. "
        f"One or more anchor policies are below threshold. "
        f"Not recommended for immediate shortlist."
    )


def generate_reasoning(
    score: FusionScore,
    intel: CandidateIntelligence,
    policy_results: list,
) -> CandidateReasoning:
    """
    Generate full structured reasoning for one ranked candidate.
    """
    technical_summary, tech_strengths, tech_concerns = \
        _build_technical_summary(policy_results, intel)

    career_summary, career_strengths, career_concerns = \
        _build_career_summary(policy_results, intel)

    availability_summary, avail_strengths, avail_concerns = \
        _build_availability_summary(policy_results, intel)

    risk_summary, risk_strengths, risk_concerns = \
        _build_risk_summary(policy_results, intel)

    all_strengths = tech_strengths + career_strengths + \
                    avail_strengths + risk_strengths
    all_concerns = tech_concerns + career_concerns + \
                   avail_concerns + risk_concerns

    return CandidateReasoning(
        candidate_id=intel.candidate_id,
        candidate_name=intel.name,
        rank=score.rank,
        tier=score.tier,
        fusion_score=score.fusion_score,
        headline=_build_headline(score, intel),
        technical_summary=technical_summary,
        career_summary=career_summary,
        availability_summary=availability_summary,
        risk_summary=risk_summary,
        conflict_summary=_build_conflict_summary(score),
        overall_verdict=_build_overall_verdict(score, intel),
        key_strengths=all_strengths[:6],
        key_concerns=all_concerns[:4],
    )


def print_reasoning(reasoning: CandidateReasoning) -> None:
    """Pretty-print one candidate's reasoning."""
    print(f"\n{'='*72}")
    print(f"  {reasoning.headline}")
    print(f"{'='*72}")
    print(f"\n  Technical  : {reasoning.technical_summary}")
    print(f"  Career     : {reasoning.career_summary}")
    print(f"  Availability: {reasoning.availability_summary}")
    print(f"  Risk       : {reasoning.risk_summary}")
    if reasoning.conflict_summary != "No conflicts requiring resolution.":
        print(f"  Conflicts  : {reasoning.conflict_summary}")
    print(f"\n  Strengths:")
    for s in reasoning.key_strengths:
        print(f"    + {s}")
    print(f"  Concerns:")
    for c in reasoning.key_concerns:
        print(f"    - {c}")
    print(f"\n  Verdict: {reasoning.overall_verdict}")
