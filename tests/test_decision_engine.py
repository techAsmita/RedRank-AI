from __future__ import annotations

from src.ingestion.loader import load_json
from src.ingestion.parser import parse_candidates
from src.features.intelligence_extractor import extract_intelligence
from src.job_intelligence.loader import load_job_description
from src.job_intelligence.parser import parse_job_description
from src.evidence.extractor import build_evidence_graph

from src.decision.context import DecisionContext
from src.decision.evaluator import DecisionEvaluator

from src.decision.policies.technical_fit import TechnicalFitPolicy
from src.decision.policies.production_readiness import ProductionReadinessPolicy
from src.decision.policies.hiring_readiness import HiringReadinessPolicy
from src.decision.policies.career_trajectory import CareerTrajectoryPolicy
from src.decision.policies.professional_signals import ProfessionalSignalsPolicy
from src.decision.policies.evidence_strength import EvidenceStrengthPolicy
from src.decision.policies.jd_intent_coverage import JDIntentCoveragePolicy
from src.decision.policies.risk_assessment import RiskAssessmentPolicy


ALL_POLICIES = lambda: [
    TechnicalFitPolicy(),
    ProductionReadinessPolicy(),
    HiringReadinessPolicy(),
    CareerTrajectoryPolicy(),
    ProfessionalSignalsPolicy(),
    EvidenceStrengthPolicy(),
    JDIntentCoveragePolicy(),
    RiskAssessmentPolicy(),
]


def _build_context_for(candidate_id: str) -> DecisionContext:
    """Build a real DecisionContext for one sample candidate."""
    records = load_json("data/sample/sample_candidates.json")
    candidates = parse_candidates(records)
    candidate = next(c for c in candidates if c.profile.candidate_id == candidate_id)

    jd_text = load_job_description("data/sample/job_description.md")
    job_intent = parse_job_description(jd_text)

    intel = extract_intelligence(candidate)
    evidence_graph = build_evidence_graph(intel, job_intent)

    return DecisionContext(
        candidate_intelligence=intel,
        job_intent=job_intent,
        evidence_graph=evidence_graph,
    )


def _print_policy_results(candidate_id: str, summary):
    print(f"\n{'='*70}")
    print(f"  DECISION POLICY ENGINE — {candidate_id}")
    print(f"{'='*70}")
    for result in summary.policy_results:
        print(f"\n  {result.policy_name}")
        print(f"    Status      : {result.status.value}")
        print(f"    Confidence  : {result.confidence}")
        print(f"    Evidence    : {len(result.supporting_evidence)} items")
        for e in result.supporting_evidence:
            print(f"      + [{e.field}] {e.explanation}")
        print(f"    Concerns    : {len(result.concerns)} items")
        for c in result.concerns:
            print(f"      - [{c.field}] {c.explanation}")


def test_decision_engine_all_8_policies_all_candidates():
    """Run all 8 policies against all 5 real candidates."""
    evaluator = DecisionEvaluator(ALL_POLICIES())

    for candidate_id in ["C001", "C002", "C003", "C004", "C005"]:
        context = _build_context_for(candidate_id)
        summary = evaluator.evaluate(context)

        assert len(summary.policy_results) == 8
        for result in summary.policy_results:
            assert result.confidence is not None
            assert 0.0 <= result.confidence <= 1.0
            # Evidence discipline: every PASS/PARTIAL must have at least
            # some referenced evidence or an explicit concern explaining the gap
            assert len(result.supporting_evidence) > 0 or len(result.concerns) > 0

        _print_policy_results(candidate_id, summary)


def test_strong_candidate_passes_most_policies():
    """C003 (PhD, Microsoft, 7yr) should not FAIL any policy."""
    context = _build_context_for("C003")
    evaluator = DecisionEvaluator(ALL_POLICIES())
    summary = evaluator.evaluate(context)

    failing = [r for r in summary.policy_results if r.status.value == "FAIL"]
    assert len(failing) == 0, f"Unexpected failures: {[r.policy_name for r in failing]}"


def test_weak_candidate_shows_risk_concerns():
    """C004 (fresher, 44 skills, 0.2y exp) should show risk concerns."""
    context = _build_context_for("C004")
    evaluator = DecisionEvaluator([RiskAssessmentPolicy(), CareerTrajectoryPolicy()])
    summary = evaluator.evaluate(context)

    risk_result = next(r for r in summary.policy_results if r.policy_name == "Risk Assessment")
    assert len(risk_result.concerns) > 0


def test_evidence_strength_reflects_profile_completeness():
    """C003 (95% complete, well-documented) should score higher evidence strength than C002 (sparse profile)."""
    evaluator = DecisionEvaluator([EvidenceStrengthPolicy()])

    c003_summary = evaluator.evaluate(_build_context_for("C003"))
    c002_summary = evaluator.evaluate(_build_context_for("C002"))

    assert c003_summary.policy_results[0].confidence >= c002_summary.policy_results[0].confidence
