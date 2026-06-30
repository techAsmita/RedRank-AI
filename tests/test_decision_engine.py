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


def test_decision_engine_real_pipeline_all_candidates():
    """Run the full 4-policy Decision Engine against all 5 real candidates."""
    evaluator = DecisionEvaluator([
        TechnicalFitPolicy(),
        ProductionReadinessPolicy(),
        HiringReadinessPolicy(),
        CareerTrajectoryPolicy(),
    ])

    for candidate_id in ["C001", "C002", "C003", "C004", "C005"]:
        context = _build_context_for(candidate_id)
        summary = evaluator.evaluate(context)

        assert len(summary.policy_results) == 4
        for result in summary.policy_results:
            assert result.confidence is not None
            assert 0.0 <= result.confidence <= 1.0

        _print_policy_results(candidate_id, summary)


def test_strong_candidate_passes_most_policies():
    """C003 (PhD, Microsoft, 7yr) should PASS or PARTIAL on most policies."""
    context = _build_context_for("C003")
    evaluator = DecisionEvaluator([
        TechnicalFitPolicy(),
        ProductionReadinessPolicy(),
        CareerTrajectoryPolicy(),
    ])
    summary = evaluator.evaluate(context)

    failing = [r for r in summary.policy_results if r.status.value == "FAIL"]
    assert len(failing) == 0


def test_weak_candidate_shows_concerns():
    """C004 (fresher, 0.2y exp) should show concerns in career trajectory."""
    context = _build_context_for("C004")
    evaluator = DecisionEvaluator([CareerTrajectoryPolicy()])
    summary = evaluator.evaluate(context)

    result = summary.policy_results[0]
    assert len(result.concerns) > 0
