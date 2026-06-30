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
from src.decision.explanation import explain_candidate, print_candidate_explanation

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


def test_full_pipeline_no_mocks_all_candidates():
    """
    The complete Phase 4 chain, exactly as specified:

    Candidate -> CandidateIntelligence -> EvidenceGraph -> JobIntent
              -> DecisionContext -> 8 Policies -> Validator -> Explanation

    No mocks anywhere. Every step uses real objects from Phases 1-4.
    """
    # Step 1: Load real candidates (Phase 1)
    records = load_json("data/sample/sample_candidates.json")
    candidates = parse_candidates(records)
    assert len(candidates) == 5

    # Step 2: Load real JD and parse JobIntent (Phase 3)
    jd_text = load_job_description("data/sample/job_description.md")
    job_intent = parse_job_description(jd_text)
    assert job_intent.metadata.title is not None

    evaluator = DecisionEvaluator(_all_policies())
    validator = EvidenceValidator()

    all_valid = True
    all_explanations = []

    for candidate in candidates:
        # Step 3: CandidateIntelligence (Phase 2)
        intel = extract_intelligence(candidate)
        assert intel.candidate_id is not None

        # Step 4: EvidenceGraph (Phase 3)
        evidence_graph = build_evidence_graph(intel, job_intent)
        assert evidence_graph.candidate_id == intel.candidate_id

        # Step 5: DecisionContext (Phase 4)
        context = DecisionContext(
            candidate_intelligence=intel,
            job_intent=job_intent,
            evidence_graph=evidence_graph,
        )

        # Step 6: 8 Policies (Phase 4)
        summary = evaluator.evaluate(context)
        assert len(summary.policy_results) == 8

        # Step 7: Validator (Phase 4)
        report = validator.validate(summary.policy_results)
        if not report.is_valid:
            all_valid = False
            print(f"\nVALIDATION FAILED for {intel.candidate_id}:")
            for err in report.errors:
                print(f"  ERROR [{err.policy_name}] {err.issue}")

        # Step 8: Explanation (Phase 4)
        explanation = explain_candidate(
            candidate_id=intel.candidate_id,
            candidate_name=intel.name,
            results=summary.policy_results,
        )
        all_explanations.append(explanation)

    # Final assertions: every step succeeded for every candidate
    assert all_valid, "One or more candidates failed evidence validation"
    assert len(all_explanations) == 5

    print(f"\n{'#'*72}")
    print("  PHASE 4 — FULL END-TO-END PIPELINE VALIDATION")
    print(f"{'#'*72}")
    print(f"\n  Candidates processed : 5/5")
    print(f"  Policies per candidate: 8/8")
    print(f"  Validation passed    : {all_valid}")
    print(f"  Explanations generated: {len(all_explanations)}/5")

    for explanation in all_explanations:
        print_candidate_explanation(explanation)
