"""
explanation.py
----------------
Recruiter-friendly explanation generator.

Converts a list of PolicyResult objects into structured,
human-readable explanations a recruiter can scan in seconds.

No LLM calls. No external templates. Every sentence is built
deterministically from the evidence/concerns already attached
to each PolicyResult, so the explanation is always traceable
back to a specific fact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from src.decision.models import PolicyResult, PolicyStatus


@dataclass
class PolicyExplanation:
    """Recruiter-friendly explanation for a single policy result."""
    policy_name: str
    status: str
    confidence: float
    evidence_summary: List[str] = field(default_factory=list)
    concern_summary: List[str] = field(default_factory=list)
    recruiter_summary: str = ""


@dataclass
class CandidateExplanation:
    """Full explanation set for one candidate across all policies."""
    candidate_id: Optional[str] = None
    candidate_name: Optional[str] = None
    policy_explanations: List[PolicyExplanation] = field(default_factory=list)
    overall_summary: str = ""


# ── Status-to-phrase mapping ──────────────────────────────────────────────────

_STATUS_PHRASES = {
    PolicyStatus.PASS: "clearly satisfies",
    PolicyStatus.PARTIAL: "partially satisfies",
    PolicyStatus.FAIL: "does not satisfy",
}


def _confidence_label(confidence: float) -> str:
    if confidence >= 0.75:
        return "high confidence"
    if confidence >= 0.45:
        return "moderate confidence"
    return "low confidence"


def explain_policy_result(result: PolicyResult) -> PolicyExplanation:
    """
    Build a deterministic, recruiter-friendly explanation for one policy.
    """
    evidence_lines = [
        f"{e.field}: {e.explanation}" for e in result.supporting_evidence
    ]
    concern_lines = [
        f"{c.field}: {c.explanation}" for c in result.concerns
    ]

    phrase = _STATUS_PHRASES[result.status]
    conf_label = _confidence_label(result.confidence)

    if result.supporting_evidence and result.concerns:
        summary = (
            f"{result.policy_name} {phrase} this requirement with {conf_label} "
            f"({result.confidence:.2f}). Supported by {len(result.supporting_evidence)} "
            f"piece(s) of evidence, with {len(result.concerns)} concern(s) noted."
        )
    elif result.supporting_evidence:
        summary = (
            f"{result.policy_name} {phrase} this requirement with {conf_label} "
            f"({result.confidence:.2f}), backed by {len(result.supporting_evidence)} "
            f"piece(s) of evidence."
        )
    elif result.concerns:
        summary = (
            f"{result.policy_name} {phrase} this requirement with {conf_label} "
            f"({result.confidence:.2f}). {len(result.concerns)} concern(s) identified: "
            f"{result.concerns[0].explanation}"
        )
    else:
        summary = (
            f"{result.policy_name} returned {result.status.value} with "
            f"{conf_label} ({result.confidence:.2f}), but no detailed evidence was recorded."
        )

    return PolicyExplanation(
        policy_name=result.policy_name,
        status=result.status.value,
        confidence=result.confidence,
        evidence_summary=evidence_lines,
        concern_summary=concern_lines,
        recruiter_summary=summary,
    )


def _build_overall_summary(
    candidate_name: Optional[str],
    explanations: List[PolicyExplanation],
) -> str:
    """
    Build one final paragraph summarizing the candidate across all policies.
    """
    name = candidate_name or "This candidate"

    passes = [e for e in explanations if e.status == "PASS"]
    partials = [e for e in explanations if e.status == "PARTIAL"]
    fails = [e for e in explanations if e.status == "FAIL"]

    avg_confidence = (
        round(sum(e.confidence for e in explanations) / len(explanations), 2)
        if explanations else 0.0
    )

    parts = [
        f"{name} passes {len(passes)} of {len(explanations)} hiring policies "
        f"(average confidence {avg_confidence:.2f})."
    ]

    if fails:
        fail_names = ", ".join(e.policy_name for e in fails)
        parts.append(f"Notable gaps: {fail_names}.")

    if partials:
        partial_names = ", ".join(e.policy_name for e in partials)
        parts.append(f"Partial matches requiring review: {partial_names}.")

    if not fails and not partials:
        parts.append("No outstanding concerns across any evaluated policy.")

    return " ".join(parts)


def explain_candidate(
    candidate_id: Optional[str],
    candidate_name: Optional[str],
    results: List[PolicyResult],
) -> CandidateExplanation:
    """
    Build the full structured explanation for one candidate
    across all policy results.
    """
    policy_explanations = [explain_policy_result(r) for r in results]
    overall = _build_overall_summary(candidate_name, policy_explanations)

    return CandidateExplanation(
        candidate_id=candidate_id,
        candidate_name=candidate_name,
        policy_explanations=policy_explanations,
        overall_summary=overall,
    )


def print_candidate_explanation(explanation: CandidateExplanation) -> None:
    """Pretty-print a CandidateExplanation to the console."""
    print(f"\n{'='*72}")
    print(f"  EXPLANATION — {explanation.candidate_name} ({explanation.candidate_id})")
    print(f"{'='*72}")

    for pe in explanation.policy_explanations:
        print(f"\n  {pe.policy_name}")
        print(f"    Status     : {pe.status}")
        print(f"    Confidence : {pe.confidence}")
        print(f"    Summary    : {pe.recruiter_summary}")
        if pe.evidence_summary:
            print(f"    Evidence:")
            for line in pe.evidence_summary:
                print(f"      + {line}")
        if pe.concern_summary:
            print(f"    Concerns:")
            for line in pe.concern_summary:
                print(f"      - {line}")

    print(f"\n  OVERALL: {explanation.overall_summary}")
    print()
