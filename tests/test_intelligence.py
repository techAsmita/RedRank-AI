from __future__ import annotations

import json
from dataclasses import asdict

from src.ingestion.loader import load_json
from src.ingestion.parser import parse_candidates
from src.features.intelligence_extractor import extract_intelligence
from src.features.intelligence_models import CandidateIntelligence


def _pretty(intel: CandidateIntelligence):
    """Pretty print a CandidateIntelligence object."""
    d = asdict(intel)
    print(f"\n{'='*60}")
    print(f"  {intel.name} ({intel.candidate_id})")
    print(f"{'='*60}")
    for section, values in d.items():
        if isinstance(values, dict):
            print(f"\n  [{section.upper()}]")
            for k, v in values.items():
                print(f"    {k:<35} {v}")
    print()


def test_intelligence_all_candidates():
    """Extract and pretty-print intelligence for all 5 sample candidates."""
    records = load_json("data/sample/sample_candidates.json")
    candidates = parse_candidates(records)
    assert len(candidates) == 5

    for candidate in candidates:
        intel = extract_intelligence(candidate)
        assert isinstance(intel, CandidateIntelligence)
        assert intel.candidate_id is not None
        _pretty(intel)


def test_risk_flags_for_inflated_profile():
    """C004 should trigger skill inflation and suspicious skill count."""
    records = load_json("data/sample/sample_candidates.json")
    candidates = parse_candidates(records)
    c004 = next(c for c in candidates if c.profile.candidate_id == "C004")
    intel = extract_intelligence(c004)
    assert intel.risk.skill_inflation_flag is True
    assert intel.risk.suspicious_skill_count is True
    assert intel.risk.risk_flag_count >= 2


def test_senior_candidate_signals():
    """C003 (PhD, Microsoft) should show strong technical and education signals."""
    records = load_json("data/sample/sample_candidates.json")
    candidates = parse_candidates(records)
    c003 = next(c for c in candidates if c.profile.candidate_id == "C003")
    intel = extract_intelligence(c003)
    assert intel.education.degree_tier == 5
    assert intel.education.is_elite_institution is True
    assert intel.technical.has_ranking is True
    assert intel.technical.has_evaluation is True
    assert intel.technical.has_production_ai is True
    assert intel.behavior.has_ai_certifications is True
