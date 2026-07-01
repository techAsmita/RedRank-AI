"""
ranker.py
----------
Top-100 generator with deterministic tie-breaking.

Takes a list of FusionScore objects and produces
a final ordered RankingOutput.

Tie-breaking order (applied when fusion_score equal to 3dp):
1. notice_period_days ascending (shorter notice wins)
2. last_active_days ascending (more recently active wins)
3. total_experience_years descending (more experience wins)
4. candidate_id ascending (deterministic, reproducible)

The last tiebreaker guarantees identical ranking across
multiple runs on identical input — critical for competition
reproducibility.
"""

from __future__ import annotations

import logging
from typing import Optional

from src.features.intelligence_models import CandidateIntelligence
from src.fusion.models import (
    FusionScore,
    RankingOutput,
    TIER_1,
    TIER_2,
    TIER_3,
    TIER_GATE,
)

logger = logging.getLogger(__name__)

# Maximum candidates to include in submission
TOP_N = 100

# Tier ordering for sort priority (lower = better)
TIER_ORDER = {
    TIER_1: 0,
    TIER_2: 1,
    TIER_3: 2,
    TIER_GATE: 3,
}


def _tier_order(score: FusionScore) -> int:
    return TIER_ORDER.get(score.tier, 3)


def _tiebreak_key(
    score: FusionScore,
    intel_map: dict,
) -> tuple:
    """
    Build a tiebreak tuple for deterministic ordering.

    Lower tuple = higher rank.

    We negate fusion_score so that higher scores sort first
    when Python's default ascending sort is applied.
    """
    intel = intel_map.get(score.candidate_id)

    notice = 999
    last_active = 999
    experience = 0.0
    candidate_id = score.candidate_id or ""

    if intel:
        notice = intel.behavior.notice_period_days or 999
        last_active = intel.behavior.last_active_days or 999
        experience = intel.career.total_experience_years or 0.0

    return (
        _tier_order(score),           # Tier first (Tier 1 before Tier 2)
        -round(score.fusion_score, 3),  # Higher score = better (negated)
        notice,                        # Shorter notice = better
        last_active,                   # More recent = better
        -experience,                   # More experience = better (negated)
        candidate_id,                  # Deterministic final tiebreak
    )


def rank_candidates(
    fusion_scores: list,
    intelligence_list: list,
    top_n: int = TOP_N,
) -> RankingOutput:
    """
    Produce the final ranked list from FusionScore objects.

    Args:
        fusion_scores: List[FusionScore] from DecisionFusionEngine
        intelligence_list: List[CandidateIntelligence] for tiebreak data
        top_n: Number of candidates to include (default 100)

    Returns:
        RankingOutput with ranked_candidates, metadata, and counts
    """
    # Build lookup map for tiebreak signals
    intel_map = {
        intel.candidate_id: intel
        for intel in intelligence_list
    }

    # Sort by tier → fusion_score → tiebreakers
    sorted_scores = sorted(
        fusion_scores,
        key=lambda s: _tiebreak_key(s, intel_map),
    )

    # Assign final ranks
    for rank, score in enumerate(sorted_scores, start=1):
        score.rank = rank

    # Take top N
    top_candidates = sorted_scores[:top_n]

    # Build metadata
    tier_counts = {TIER_1: 0, TIER_2: 0, TIER_3: 0, TIER_GATE: 0}
    for score in sorted_scores:
        tier_counts[score.tier] = tier_counts.get(score.tier, 0) + 1

    output = RankingOutput(
        ranked_candidates=top_candidates,
        total_candidates=len(fusion_scores),
        gate_failures=tier_counts.get(TIER_GATE, 0),
        tier_1_count=tier_counts.get(TIER_1, 0),
        tier_2_count=tier_counts.get(TIER_2, 0),
        tier_3_count=tier_counts.get(TIER_3, 0),
    )

    logger.info(
        "Ranking complete — total=%d | T1=%d | T2=%d | T3=%d | gates=%d | top_%d selected",
        output.total_candidates,
        output.tier_1_count,
        output.tier_2_count,
        output.tier_3_count,
        output.gate_failures,
        top_n,
    )

    return output


def print_ranking_summary(output: RankingOutput) -> None:
    """Print a human-readable ranking summary to console."""
    print(f"\n{'='*72}")
    print("  RANKING SUMMARY")
    print(f"{'='*72}")
    print(f"  Total candidates processed : {output.total_candidates}")
    print(f"  Gate failures              : {output.gate_failures}")
    print(f"  Tier 1 (strong)            : {output.tier_1_count}")
    print(f"  Tier 2 (competitive)       : {output.tier_2_count}")
    print(f"  Tier 3 (weak)              : {output.tier_3_count}")
    print(f"\n  TOP 10 CANDIDATES:")
    print(f"  {'Rank':<6} {'ID':<16} {'Name':<25} {'Tier':<10} {'Score':<8} {'Reasoning'}")
    print(f"  {'-'*100}")

    for score in output.ranked_candidates[:10]:
        print(
            f"  {score.rank:<6} "
            f"{score.candidate_id:<16} "
            f"{(score.candidate_name or 'Unknown'):<25} "
            f"{score.tier:<10} "
            f"{score.fusion_score:<8.4f} "
            f"{score.reasoning[:60]}..."
        )
    print()
