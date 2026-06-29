"""Tests for the feature extractor."""

from src.ingestion.loader import load_json
from src.ingestion.parser import parse_candidates
from src.features.extractor import extract_features, CandidateFeatures


def test_extract_features_returns_dataclass():
    """Feature extraction returns a CandidateFeatures instance."""
    records = load_json("data/sample/sample_candidates.json")
    candidates = parse_candidates(records)
    features = extract_features(candidates[0])
    assert isinstance(features, CandidateFeatures)


def test_experience_computed():
    """Total experience months are computed from date ranges."""
    records = load_json("data/sample/sample_candidates.json")
    candidates = parse_candidates(records)
    features = extract_features(candidates[0])
    assert features.total_experience_months > 0
    assert features.total_experience_years > 0


def test_skills_normalized():
    """Skills are normalized and deduplicated."""
    records = load_json("data/sample/sample_candidates.json")
    candidates = parse_candidates(records)
    features = extract_features(candidates[0])
    assert features.skill_count > 0
    assert all(s == s.lower() for s in features.normalized_skills)


def test_profile_completeness():
    """Completeness score is between 0 and 1."""
    records = load_json("data/sample/sample_candidates.json")
    candidates = parse_candidates(records)
    for c in candidates:
        features = extract_features(c)
        assert 0.0 <= features.profile_completeness <= 1.0
