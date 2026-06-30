from __future__ import annotations

from src.ingestion.loader import load_json
from src.ingestion.parser import parse_candidates
from src.features.intelligence_extractor import extract_intelligence
from src.job_intelligence.loader import load_job_description
from src.job_intelligence.parser import parse_job_description
from src.evidence.extractor import build_evidence_graph
from src.evidence.printer import print_evidence_graph
from src.evidence.models import EvidenceGraph


def test_evidence_graph_all_candidates():
    """Build and print evidence graphs for all 5 candidates."""
    records = load_json("data/sample/sample_candidates.json")
    candidates = parse_candidates(records)
    jd = load_job_description("data/sample/job_description.md")
    job_intent = parse_job_description(jd)

    for candidate in candidates:
        intel = extract_intelligence(candidate)
        graph = build_evidence_graph(intel, job_intent)
        assert isinstance(graph, EvidenceGraph)
        assert graph.candidate_id is not None
        print_evidence_graph(graph)


def test_strong_candidate_has_high_evidence():
    """C003 (PhD, Microsoft, 7yr) should show strong evidence across the board."""
    records = load_json("data/sample/sample_candidates.json")
    candidates = parse_candidates(records)
    jd = load_job_description("data/sample/job_description.md")
    job_intent = parse_job_description(jd)

    c003 = next(c for c in candidates if c.profile.candidate_id == "C003")
    intel = extract_intelligence(c003)
    graph = build_evidence_graph(intel, job_intent)

    assert graph.production_ai.satisfied is True
    assert graph.experience_years.satisfied is True
    assert graph.education.strength >= 0.6
    assert graph.risk_flags.strength >= 0.8


def test_inflated_candidate_has_risk_flags():
    """C004 (fresher with 44 skills) should show risk flags."""
    records = load_json("data/sample/sample_candidates.json")
    candidates = parse_candidates(records)
    jd = load_job_description("data/sample/job_description.md")
    job_intent = parse_job_description(jd)

    c004 = next(c for c in candidates if c.profile.candidate_id == "C004")
    intel = extract_intelligence(c004)
    graph = build_evidence_graph(intel, job_intent)

    assert graph.risk_flags.satisfied is False
    assert graph.experience_years.satisfied is False
