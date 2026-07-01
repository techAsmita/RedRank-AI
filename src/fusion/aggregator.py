"""
aggregator.py
--------------
Computes tier score (anchor minimum) and booster score
from the 8 policy results.

Design:
- Anchor score = min() of 4 anchor policy confidences
  (forces candidates to be broadly competitive, not narrowly excellent)
- Booster score = weighted sum of 5 booster signals
  (fine-grained ordering within tier)
- Response multiplier = independent dampener on final score
  (directly implements JD's "down-weight appropriately" instruction)

No ranking logic lives here. This module only computes scores.
"""

from __future__ import annotations

from src.decision.models import PolicyResult, PolicyStatus
from src.features.intelligence_models import CandidateIntelligence
from src.fusion.models import TIER_1, TIER_2, TIER_3


# ── Policy name constants ─────────────────────────────────────────────────────

ANCHOR_POLICIES = {
    "Technical Fit",
    "Production Readiness",
    "JD Intent Coverage",
    "Career Trajectory",
}

BOOSTER_WEIGHTS = {
    "Hiring Readiness":    0.25,
    "Professional Signals": 0.20,
    "Evidence Strength":   0.20,
    "Risk Assessment":     0.20,
    "Career Trajectory":   0.15,   # also contributes as a booster
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find(results: list, name: str) -> PolicyResult:
    """Find a policy result by exact or partial name match."""
    for r in results:
        if name.lower() in r.policy_name.lower():
            return r
    return None


def _confidence(result: PolicyResult) -> float:
    """Return confidence safely, defaulting to 0.0."""
    if result is None:
        return 0.0
    return result.confidence or 0.0


# ── Anchor score ──────────────────────────────────────────────────────────────

def compute_anchor_scores(results: list) -> dict:
    """
    Compute the confidence for each of the 4 anchor policies.

    Returns a dict mapping policy name -> confidence.
    """
    anchors = {}
    for name in ["Technical Fit", "Production Readiness",
                 "JD Intent Coverage", "Career Trajectory"]:
        r = _find(results, name)
        anchors[name] = _confidence(r)
    return anchors


def compute_tier_score(anchor_scores: dict) -> float:
    """
    Tier score = minimum of the 4 anchor confidences.

    Why minimum?
    The JD says we'd rather see 10 great matches than 1000 maybes.
    A candidate with 0.95 technical fit and 0.20 production readiness
    is not a great match — they are the "researcher who can't ship"
    anti-pattern the JD warns against twice.

    The minimum forces candidates to be broadly competitive.
    """
    if not anchor_scores:
        return 0.0
    return round(min(anchor_scores.values()), 3)


def assign_tier(tier_score: float) -> str:
    """
    Assign a tier label based on anchor minimum.

    TIER_1: all anchors strong (≥ 0.65)
    TIER_2: competitive but mixed (≥ 0.40)
    TIER_3: one or more anchors weak (< 0.40)
    """
    if tier_score >= 0.65:
        return TIER_1
    if tier_score >= 0.40:
        return TIER_2
    return TIER_3


# ── Booster score ─────────────────────────────────────────────────────────────

def compute_booster_scores(results: list) -> dict:
    """
    Compute individual booster contributions.

    Returns a dict mapping policy name -> weighted contribution.
    """
    booster_scores = {}
    for name, weight in BOOSTER_WEIGHTS.items():
        r = _find(results, name)
        conf = _confidence(r)
        booster_scores[name] = round(conf * weight, 3)
    return booster_scores


def compute_booster_total(booster_scores: dict) -> float:
    """Sum all booster contributions into one composite score."""
    return round(sum(booster_scores.values()), 3)


# ── Response rate multiplier ──────────────────────────────────────────────────

def compute_response_multiplier(intel: CandidateIntelligence) -> float:
    """
    Response rate multiplier — independent dampener on fusion score.

    JD: 'a perfect-on-paper candidate who hasn't logged in for 6 months
         and has a 5% recruiter response rate is, for hiring purposes,
         not actually available. Down-weight them appropriately.'

    We implement this as a multiplier (not additive) so that
    low response rate genuinely suppresses even top-tier technical
    candidates, rather than being offset by other boosters.

    Floor of 0.50: even zero-response candidates can still rank
    (JD says 30+ day notice is 'still in scope but the bar gets higher',
    implying deprioritization, not elimination).
    """
    rr = intel.behavior.response_rate

    if rr is None:
        return 0.75   # Unknown response rate: moderate penalty

    # Scale linearly from 0.50 (at rr=0) to 1.0 (at rr=1.0)
    multiplier = 0.50 + (rr * 0.50)
    return round(min(max(multiplier, 0.50), 1.0), 3)


# ── Final fusion score ────────────────────────────────────────────────────────

def compute_fusion_score(
    tier_score: float,
    booster_total: float,
    response_multiplier: float,
) -> float:
    """
    Final fusion score combining tier, boosters, and availability.

    fusion_score = (tier*0.70 + booster*0.30) * response_multiplier

    Why 70/30 split?
    Tier score (anchor minimum) represents fundamental fit.
    Booster score represents fine-grained differentiation.
    A 70/30 split ensures strong fundamental fit dominates,
    while boosters provide meaningful separation within tiers.
    """
    raw = (tier_score * 0.70) + (booster_total * 0.30)
    return round(raw * response_multiplier, 4)
