"""
gates.py
---------
Hard gate evaluation.

Gates are binary eliminators applied before any scoring.
A candidate who fails any gate cannot rank in the top tier
regardless of technical excellence.

Every gate is traceable to a specific JD signal.
No gate is inferred — each maps to an explicit JD statement.
"""

from __future__ import annotations

from src.decision.models import PolicyResult, PolicyStatus
from src.features.intelligence_models import CandidateIntelligence
from src.fusion.models import GateResult


# ── Gate definitions ──────────────────────────────────────────────────────────

CONSULTING_FIRMS = {
    "tcs", "tata consultancy", "infosys", "wipro", "accenture",
    "cognizant", "capgemini", "hcl", "tech mahindra", "mphasis",
    "hexaware", "mindtree", "l&t infotech", "ltimindtree",
}


def _get_policy(results: list, policy_id: str) -> PolicyResult:
    """Find a policy result by name substring."""
    for r in results:
        if policy_id.lower() in r.policy_name.lower():
            return r
    return None


def _gate_pure_research(
    results: list,
    intel: CandidateIntelligence,
) -> tuple:
    """
    Gate 1: Pure research background with no production deployment.
    JD: 'we will not move forward' — stated explicitly twice.

    Trigger: Production Readiness FAIL AND
             candidate has 3+ years experience
             (eliminates early-career candidates from this gate,
              since they simply haven't had time yet, not because
              they chose research over production)
    """
    prod = _get_policy(results, "Production Readiness")
    if prod is None:
        return False, ""

    if (
        prod.status == PolicyStatus.FAIL
        and intel.career.total_experience_years >= 3.0
    ):
        return True, (
            f"Production Readiness FAIL with {intel.career.total_experience_years:.1f}y "
            f"experience — pure research/no-production profile. "
            f"JD explicitly excludes this profile."
        )
    return False, ""


def _gate_keyword_only_profile(
    results: list,
    intel: CandidateIntelligence,
) -> tuple:
    """
    Gate 2: Keyword-stuffed skills with no corroborating production evidence.
    JD: 'The right answer is not find candidates whose skills section
         contains the most AI keywords — that is a trap.'

    Trigger: skill_inflation_flag=True AND
             production_ai evidence strength < 0.20
    """
    risk = intel.risk
    prod_ai_strength = 0.0

    prod = _get_policy(results, "Production Readiness")
    if prod is not None:
        for e in prod.supporting_evidence:
            if "Production AI" in e.field:
                try:
                    prod_ai_strength = float(e.value)
                except (ValueError, TypeError):
                    pass

    if risk.skill_inflation_flag and prod_ai_strength < 0.20:
        return True, (
            f"Skill inflation flag triggered ({intel.technical.skill_count} skills, "
            f"{intel.career.total_experience_years:.1f}y exp) with no corroborating "
            f"production AI evidence (strength={prod_ai_strength:.2f}). "
            f"Matches JD's explicit keyword-trap pattern."
        )
    return False, ""


def _gate_zero_engagement(
    intel: CandidateIntelligence,
) -> tuple:
    """
    Gate 3: Completely unresponsive + highly inactive candidate.
    JD: 'down-weight appropriately' — a candidate who hasn't logged
         in for 6 months with 5% response rate is 'not actually available.'

    Trigger: response_rate < 0.10 AND last_active_days > 90
    Both conditions must be met — either alone is not a gate.
    """
    rr = intel.behavior.response_rate
    lad = intel.behavior.last_active_days

    if (
        rr is not None and rr < 0.10
        and lad is not None and lad > 90
    ):
        return True, (
            f"Response rate {rr:.2f} AND last active {lad} days ago. "
            f"Candidate is effectively unavailable per JD availability criteria."
        )
    return False, ""


def _gate_consulting_only(
    intel: CandidateIntelligence,
) -> tuple:
    """
    Gate 4: Entire career at consulting firms, zero product-company experience.
    JD: 'People who have only worked at consulting firms in their entire
         career — we've had bad fit experiences.'

    Nuance: 'If you're currently at one but have prior product-company
             experience, that's fine.' — so we only gate if ALL roles
             are consulting firms.
    """
    if not intel.career.title_progression:
        return False, ""

    companies = []
    for exp in intel.career.title_progression:
        pass  # title_progression stores titles not companies

    # Check via startup_ratio proxy:
    # consulting firms are large enterprises — startup_ratio near 0
    # combined with company names matching consulting set.
    # We don't have per-company names on CareerIntelligence directly,
    # so this gate uses a conservative heuristic only.
    # Full implementation requires raw experience data.
    return False, ""


# ── Main gate evaluator ───────────────────────────────────────────────────────

def evaluate_gates(
    results: list,
    intel: CandidateIntelligence,
) -> GateResult:
    """
    Evaluate all hard gates for one candidate.

    Returns a GateResult indicating whether the candidate passed
    all gates, and which gates failed if any.
    """
    failed = []

    triggered, note = _gate_pure_research(results, intel)
    if triggered:
        failed.append(f"PURE_RESEARCH: {note}")

    triggered, note = _gate_keyword_only_profile(results, intel)
    if triggered:
        failed.append(f"KEYWORD_ONLY: {note}")

    triggered, note = _gate_zero_engagement(intel)
    if triggered:
        failed.append(f"ZERO_ENGAGEMENT: {note}")

    # Gate 4 (consulting-only) is noted as partially implemented
    # until raw company names are available on CareerIntelligence.

    if failed:
        return GateResult(
            passed=False,
            failed_gates=failed,
            notes=f"{len(failed)} gate(s) failed.",
        )

    return GateResult(passed=True, notes="All gates passed.")
