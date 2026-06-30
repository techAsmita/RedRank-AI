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


def _build_context_for(candidate_id: str) -> DecisionContext:
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


def test_validator_passes_for_all_real_candidates():
    """Every policy result for every sample candidate must be evidence-valid."""
    evaluator = DecisionEvaluator(_all_policies())
    validator = EvidenceValidator()

    for candidate_id in ["C001", "C002", "C003", "C004", "C005"]:
        context = _build_context_for(candidate_id)
        summary = evaluator.evaluate(context)

        report = validator.validate(summary.policy_results)

        print(f"\n{'='*60}")
        print(f"  VALIDATION — {candidate_id}")
        print(f"{'='*60}")
        print(f"  is_valid: {report.is_valid}")
        print(f"  errors:   {len(report.errors)}")
        print(f"  warnings: {len(report.warnings)}")

        for issue in report.errors:
            print(f"  ERROR   [{issue.policy_name}] {issue.issue}")
        for issue in report.warnings:
            print(f"  WARNING [{issue.policy_name}] {issue.issue}")

        assert report.is_valid, f"Validation failed for {candidate_id}: {report.errors}"


def test_validator_rejects_unsupported_pass():
    """A PASS with zero evidence/concerns must be flagged as an ERROR."""
    from src.decision.models import PolicyResult, PolicyStatus

    fake_result = PolicyResult(
        policy_name="Fake Policy",
        status=PolicyStatus.PASS,
        confidence=0.95,
        supporting_evidence=[],
        concerns=[],
        decision_trace=[],
    )

    validator = EvidenceValidator()
    report = validator.validate([fake_result])

    assert report.is_valid is False
    assert len(report.errors) == 1
    assert "Fake Policy" in report.errors[0].policy_name


def test_validator_rejects_invalid_confidence_range():
    """Confidence outside [0.0, 1.0] must be flagged."""
    from src.decision.models import PolicyResult, PolicyStatus, DecisionEvidence

    fake_result = PolicyResult(
        policy_name="Broken Policy",
        status=PolicyStatus.PASS,
        confidence=1.5,
        supporting_evidence=[DecisionEvidence(
            source="test", field="x", value="y", explanation="z",
        )],
        concerns=[],
        decision_trace=[],
    )

    validator = EvidenceValidator()
    report = validator.validate([fake_result])

    assert report.is_valid is False
    assert any("1.5" in i.issue for i in report.errors)
