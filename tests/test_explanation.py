from __future__ import annotations

from src.ingestion.loader import load_json
from src.ingestion.parser import parse_candidates
from src.features.intelligence_extractor import extract_intelligence
from src.job_intelligence.loader import load_job_description
from src.job_intelligence.parser import parse_job_description
from src.evidence.extractor import build_evidence_graph

from src.decision.context import DecisionContext
from src.decision.evaluator import DecisionEvaluator
from src.decision.validator import EvidenceValidator
from src.decision.explanation import explain_candidate, print_candidate_explanation, CandidateExplanation

from src.decision.policies.technical_fit import TechnicalFitPolicy
from src.decision.policies.production_readiness import ProductionReadinessPolicy
from src.decision.policies.hiring_readiness import HiringReadinessPolicy
from src.decision.policies.career_trajectory import CareerTrajectoryPolicy
from src.decision.policies.professional_signals import ProfessionalSignalsPolicy
from src.decision.policies.evidence_strength import EvidenceStrengthPolicy
from src.decision.policies.jd_intent_coverage import JDIntentCoveragePolicy
from src.decision.policies.risk_assessment import RiskAssessmentPolicy


def _all_policies():
    return [
        TechnicalFitPolicy(),
        ProductionReadinessPolicy(),
        HiringReadinessPolicy(),
        CareerTrajectoryPolicy(),
        ProfessionalSignalsPolicy(),
        EvidenceStrengthPolicy(),
        JDIntentCoveragePolicy(),
        RiskAssessmentPolicy(),
    ]


def _build_context_for(candidate_id: str):
    records = load_json("data/sample/sample_candidates.json")
    candidates = parse_candidates(records)
    candidate = next(c for c in candidates if c.profile.candidate_id == candidate_id)

    jd_text = load_job_description("data/sample/job_description.md")
    job_intent = parse_job_description(jd_text)

    intel = extract_intelligence(candidate)
    evidence_graph = build_evidence_graph(intel, job_intent)

    context = DecisionContext(
        candidate_intelligence=intel,
        job_intent=job_intent,
        evidence_graph=evidence_graph,
    )
    return context, intel


def test_explanation_generated_for_all_candidates():
    """Generate and print full explanations for all 5 real candidates."""
    evaluator = DecisionEvaluator(_all_policies())

    for candidate_id in ["C001", "C002", "C003", "C004", "C005"]:
        context, intel = _build_context_for(candidate_id)
        summary = evaluator.evaluate(context)

        explanation = explain_candidate(
            candidate_id=intel.candidate_id,
            candidate_name=intel.name,
            results=summary.policy_results,
        )

        assert isinstance(explanation, CandidateExplanation)
        assert len(explanation.policy_explanations) == 8
        assert explanation.overall_summary != ""

        print_candidate_explanation(explanation)


def test_strong_candidate_explanation_shows_few_gaps():
    """C003 (PhD, Microsoft) should have a mostly clean overall summary."""
    evaluator = DecisionEvaluator(_all_policies())
    context, intel = _build_context_for("C003")
    summary = evaluator.evaluate(context)

    explanation = explain_candidate(intel.candidate_id, intel.name, summary.policy_results)
    fails = [e for e in explanation.policy_explanations if e.status == "FAIL"]
    assert len(fails) == 0


def test_weak_candidate_explanation_shows_gaps():
    """C004 (fresher, 0.2y exp) should show fails or partials in overall summary."""
    evaluator = DecisionEvaluator(_all_policies())
    context, intel = _build_context_for("C004")
    summary = evaluator.evaluate(context)

    explanation = explain_candidate(intel.candidate_id, intel.name, summary.policy_results)
    weak_statuses = [
        e for e in explanation.policy_explanations
        if e.status in ("FAIL", "PARTIAL")
    ]
    assert len(weak_statuses) > 0
    assert "gap" in explanation.overall_summary.lower() or "partial" in explanation.overall_summary.lower()
