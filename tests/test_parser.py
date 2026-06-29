"""Tests for the candidate parser."""

from src.ingestion.loader import load_json
from src.ingestion.parser import parse_candidate, parse_candidates
from src.ingestion.models import Candidate


def test_parse_single_candidate():
    """A well-formed dict parses into a valid Candidate."""
    raw = {
        "candidate_id": "TEST001",
        "name": "Test User",
        "email": "test@example.com",
        "skills": {"primary": ["Python"], "secondary": ["SQL"]},
        "experience": [
            {"title": "Engineer", "company": "ACME", "start_date": "2020-01", "end_date": "present", "is_current": True}
        ]
    }
    candidate = parse_candidate(raw)
    assert candidate is not None
    assert isinstance(candidate, Candidate)
    assert candidate.profile.name == "Test User"


def test_parse_flat_skills():
    """Flat skill list parses correctly."""
    raw = {"candidate_id": "TEST002", "skills": ["Python", "ML", "NLP"]}
    candidate = parse_candidate(raw)
    assert candidate is not None
    assert "Python" in candidate.skills.all_skills


def test_parse_empty_record():
    """Empty dict produces a Candidate with defaults — does not crash."""
    candidate = parse_candidate({})
    assert candidate is not None


def test_parse_sample_file():
    """Full sample file parses without errors."""
    records = load_json("data/sample/sample_candidates.json")
    candidates = parse_candidates(records)
    assert len(candidates) == 2
