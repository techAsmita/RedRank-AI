from __future__ import annotations

from src.ingestion.loader import load_json
from src.ingestion.parser import parse_candidates


def test_real_candidates_parse_without_errors():
    """All 5 real sample candidates should parse cleanly into Candidate objects."""
    records = load_json("data/sample/real_sample_candidates.json")
    candidates = parse_candidates(records)

    assert len(candidates) == 5

    for c in candidates:
        print(f"\n{'='*60}")
        print(f"  {c.profile.candidate_id} — {c.profile.name}")
        print(f"{'='*60}")
        print(f"  Title       : {c.profile.current_title}")
        print(f"  Company     : {c.profile.current_company}")
        print(f"  Location    : {c.profile.location}, {c.profile.country}")
        print(f"  Experience  : {c.profile.years_of_experience} years")
        print(f"  Roles       : {len(c.experience)}")
        print(f"  Education   : {len(c.education)}")
        print(f"  Skills      : {len(c.skills)}")
        if c.skills:
            print(f"    sample: {c.skills[0].name} ({c.skills[0].proficiency}, {c.skills[0].endorsements} endorsements)")
        print(f"  Certs       : {len(c.certifications)}")
        print(f"  Languages   : {len(c.languages)}")
        print(f"  Notice days : {c.redrob.notice_period_days}")
        print(f"  Open to work: {c.redrob.open_to_work_flag}")
        print(f"  GitHub score: {c.redrob.github_activity_score}")

        assert c.profile.candidate_id is not None
        assert c.profile.name is not None


def test_skills_preserve_rich_evidence():
    """Real skill entries should retain proficiency, endorsements, duration."""
    records = load_json("data/sample/real_sample_candidates.json")
    candidates = parse_candidates(records)

    candidate_with_skills = next(c for c in candidates if len(c.skills) > 0)
    skill = candidate_with_skills.skills[0]

    assert skill.name is not None
    assert isinstance(skill.endorsements, int)
    assert isinstance(skill.duration_months, int)


def test_experience_from_career_history():
    """Experience should be correctly mapped from career_history key."""
    records = load_json("data/sample/real_sample_candidates.json")
    candidates = parse_candidates(records)

    candidate_with_exp = next(c for c in candidates if len(c.experience) > 0)
    exp = candidate_with_exp.experience[0]

    assert exp.title is not None
    assert exp.company is not None
