"""
models.py
----------
Data models for the Decision Fusion Engine.

These models represent the output of fusion — not the input.
Input is a list of PolicyResult objects from Phase 4.
Output is a ranked list of FusionResult objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ── Tier constants ────────────────────────────────────────────────────────────

TIER_1 = "TIER_1"   # Top candidates — all anchors strong
TIER_2 = "TIER_2"   # Competitive candidates — mixed anchors
TIER_3 = "TIER_3"   # Weak candidates — one or more anchors failing
TIER_GATE = "GATE_FAILED"   # Hard-gate failures — bottom of ranking


@dataclass
class GateResult:
    """Result of hard-gate evaluation."""
    passed: bool = True
    failed_gates: list = field(default_factory=list)
    notes: str = ""


@dataclass
class ConflictResolution:
    """
    Record of how a conflict between policies was resolved.
    Every resolution must be traceable to a rule.
    """
    conflict_type: str = ""
    description: str = ""
    action_taken: str = ""
    tier_adjustment: int = 0        # -1 = demoted one tier, 0 = no change
    confidence_adjustment: float = 0.0


@dataclass
class FusionScore:
    """
    The complete, explainable fusion output for one candidate.
    """
    candidate_id: Optional[str] = None
    candidate_name: Optional[str] = None

    # Gate
    gate_result: GateResult = field(default_factory=GateResult)

    # Tier
    tier: str = TIER_3
    tier_score: float = 0.0         # min of 4 anchor confidences
    booster_score: float = 0.0      # weighted booster composite
    response_multiplier: float = 1.0

    # Final
    fusion_score: float = 0.0       # tier*0.70 + booster*0.30 * multiplier
    rank: Optional[int] = None

    # Explainability
    anchor_scores: dict = field(default_factory=dict)
    booster_scores: dict = field(default_factory=dict)
    conflicts_resolved: list = field(default_factory=list)
    reasoning: str = ""


@dataclass
class RankingOutput:
    """
    Final output of the entire ranking pipeline.
    Contains the top-100 ranked candidates plus metadata.
    """
    ranked_candidates: list = field(default_factory=list)   # List[FusionScore]
    total_candidates: int = 0
    gate_failures: int = 0
    tier_1_count: int = 0
    tier_2_count: int = 0
    tier_3_count: int = 0
    job_title: Optional[str] = None
    notes: str = ""
