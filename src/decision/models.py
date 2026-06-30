"""
models.py
---------
Core data models for the Decision Policy Engine.

Design decisions:
- Pure data models.
- No business logic.
- Immutable wherever possible.
- Shared by every decision policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# ──────────────────────────────────────────────────────────────────────────────
# Policy Status
# ──────────────────────────────────────────────────────────────────────────────

class PolicyStatus(str, Enum):
    """
    Standard decision returned by every policy.
    """

    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"


# ──────────────────────────────────────────────────────────────────────────────
# Policy Definition
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DecisionPolicy:
    """
    Metadata describing one policy.
    """

    id: str
    name: str
    description: str
    enabled: bool = True


# ──────────────────────────────────────────────────────────────────────────────
# Supporting Evidence
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DecisionEvidence:
    """
    One verifiable piece of evidence supporting a conclusion.
    """

    source: str
    field: str
    value: str
    explanation: str


# ──────────────────────────────────────────────────────────────────────────────
# Decision Trace
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DecisionTrace:
    """
    Records how a policy reached its conclusion.
    """

    step: str
    observation: str
    outcome: str


# ──────────────────────────────────────────────────────────────────────────────
# Individual Policy Result
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class PolicyResult:
    """
    Result produced by a single decision policy.
    """

    policy_name: str

    status: PolicyStatus

    confidence: float

    supporting_evidence: list[DecisionEvidence] = field(default_factory=list)

    concerns: list[DecisionEvidence] = field(default_factory=list)

    decision_trace: list[DecisionTrace] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Overall Decision Summary
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class DecisionSummary:
    """
    Complete output of the Decision Policy Engine.

    Phase 4 intentionally does NOT include
    ranking or final recommendation.
    """

    candidate_id: str

    policy_results: list[PolicyResult] = field(default_factory=list)

    overall_observations: list[str] = field(default_factory=list)
