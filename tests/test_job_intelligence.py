"""
test_job_intelligence.py

End-to-end test for the Job Intent Engine.
"""

from pathlib import Path

from src.job_intelligence.loader import load_job_description
from src.job_intelligence.parser import parse_job_description


def test_job_intent_extraction():

    jd_path = Path("data/sample/job_description.md")

    jd = load_job_description(jd_path)

    intent = parse_job_description(jd)

    print("\n")
    print("=" * 70)
    print("JOB INTENT")
    print("=" * 70)

    print("\n[METADATA]")
    print(f"Title                 : {intent.metadata.title}")

    print("\n[TECHNICAL]")
    print(f"Years                 : {intent.technical.minimum_years}")
    print(f"Skills                : {intent.technical.required_skills}")
    print(f"Categories            : {intent.technical.skill_categories}")

    print(f"Python                : {intent.technical.python_required}")
    print(f"Retrieval             : {intent.technical.retrieval}")
    print(f"Evaluation            : {intent.technical.evaluation}")
    print(f"MLOps                 : {intent.technical.mlops}")
    print(f"Cloud                 : {intent.technical.cloud_required}")
    print(f"Production AI         : {intent.technical.production_ai}")

    print("\n[CAREER]")
    print(f"Minimum Experience    : {intent.career.minimum_experience_years}")
    print(f"Startup               : {intent.career.startup_background}")
    print(f"Enterprise            : {intent.career.enterprise_background}")
    print(f"Research              : {intent.career.research_background}")
    print(f"Management            : {intent.career.management_background}")

    print("\n[BEHAVIOR]")
    print(f"Ownership             : {intent.behavior.ownership}")
    print(f"Product Mindset       : {intent.behavior.product_mindset}")
    print(f"Communication         : {intent.behavior.communication}")
    print(f"Learning              : {intent.behavior.learning_mindset}")
    print(f"Cross Functional      : {intent.behavior.cross_functional}")
    print(f"Customer Focus        : {intent.behavior.customer_focus}")
    print(f"Problem Solving       : {intent.behavior.problem_solving}")
    print(f"Ambiguity             : {intent.behavior.ambiguity_tolerance}")

    assert len(intent.raw_text) > 0
    