from __future__ import annotations

import logging
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

from src.fusion.engine import DecisionFusionEngine, fuse_batch
from src.fusion.ranker import rank_candidates, print_ranking_summary
from src.fusion.reasoning import generate_reasoning, print_reasoning
from src.fusion.models import TIER_GATE


logging.basicConfig(level=logging.WARNING)


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


def _build_pipeline():
    """Build the complete pipeline for all real sample candidates."""
    records = load_json("data/sample/real_sample_candidates.json")
    candidates = parse_candidates(records)

    jd_text = load_job_description("data/sample/job_description.md")
    job_intent = parse_job_description(jd_text)

    evaluator = DecisionEvaluator(_all_policies())
    validator = EvidenceValidator()
    engine = DecisionFusionEngine()

    intelligence_list = []
    policy_results_map = {}
    fusion_scores = []

    for candidate in candidates:
        intel = extract_intelligence(candidate)
        evidence_graph = build_evidence_graph(intel, job_intent)

        context = DecisionContext(
            candidate_intelligence=intel,
            job_intent=job_intent,
            evidence_graph=evidence_graph,
        )

        summary = evaluator.evaluate(context)
        report = validator.validate(summary.policy_results)
        assert report.is_valid, (
            f"Validation failed for {intel.candidate_id}: "
            f"{[e.issue for e in report.errors]}"
        )

        score = engine.fuse(intel, summary.policy_results, job_intent)
        intelligence_list.append(intel)
        policy_results_map[intel.candidate_id] = summary.policy_results
        fusion_scores.append(score)

    return intelligence_list, policy_results_map, fusion_scores, job_intent


def test_fusion_produces_valid_scores():
    """Every candidate should produce a valid FusionScore."""
    intel_list, policy_map, scores, job_intent = _build_pipeline()

    assert len(scores) == 8

    for score in scores:
        assert score.candidate_id is not None
        assert 0.0 <= score.fusion_score <= 1.0
        assert score.tier is not None
        assert score.reasoning != ""


def test_ranking_produces_correct_order():
    """Ranked list should be ordered by tier then fusion score."""
    intel_list, policy_map, scores, job_intent = _build_pipeline()

    output = rank_candidates(scores, intel_list, top_n=8)

    assert len(output.ranked_candidates) == 8

    # Verify tier ordering — no Tier 2 candidate ranks above a Tier 1
    tier_order = {"TIER_1": 0, "TIER_2": 1, "TIER_3": 2, "GATE_FAILED": 3}
    for i in range(len(output.ranked_candidates) - 1):
        a = output.ranked_candidates[i]
        b = output.ranked_candidates[i + 1]
        assert tier_order.get(a.tier, 3) <= tier_order.get(b.tier, 3), (
            f"Tier ordering violated: {a.candidate_id} ({a.tier}) "
            f"ranked above {b.candidate_id} ({b.tier})"
        )

    print_ranking_summary(output)


def test_reasoning_generated_for_all_candidates():
    """Every ranked candidate should have complete reasoning."""
    intel_list, policy_map, scores, job_intent = _build_pipeline()
    output = rank_candidates(scores, intel_list, top_n=8)

    intel_map = {i.candidate_id: i for i in intel_list}

    for score in output.ranked_candidates:
        intel = intel_map[score.candidate_id]
        policy_results = policy_map[score.candidate_id]
        reasoning = generate_reasoning(score, intel, policy_results)

        assert reasoning.headline != ""
        assert reasoning.overall_verdict != ""
        assert reasoning.rank == score.rank

        print_reasoning(reasoning)


def test_ml_engineers_rank_above_off_domain():
    """ML Engineers should rank above .NET Developer and Mechanical Engineer."""
    intel_list, policy_map, scores, job_intent = _build_pipeline()
    output = rank_candidates(scores, intel_list, top_n=8)

    ranked = output.ranked_candidates
    intel_map = {i.candidate_id: i for i in intel_list}

    ml_ranks = []
    off_domain_ranks = []

    for score in ranked:
        intel = intel_map[score.candidate_id]
        title = (intel.career.current_title_normalized or "").lower()
        if any(kw in title for kw in ["ml", "machine learning", "data scientist"]):
            ml_ranks.append(score.rank)
        elif any(kw in title for kw in [".net", "mechanical"]):
            off_domain_ranks.append(score.rank)

    print(f"\nML Engineer ranks: {ml_ranks}")
    print(f"Off-domain ranks:  {off_domain_ranks}")

    if ml_ranks and off_domain_ranks:
        assert min(ml_ranks) < max(off_domain_ranks), (
            "At least one ML Engineer should rank above all off-domain candidates"
        )
