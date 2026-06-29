from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from src.ingestion.models import Candidate, Experience
from src.features.intelligence_models import (
    CandidateIntelligence,
    TechnicalIntelligence,
    CareerIntelligence,
    EducationIntelligence,
    BehaviorIntelligence,
    RiskIntelligence,
)
from src.features.preprocessing import (
    normalize_title,
    normalize_company,
    parse_date,
    duration_in_months,
)

logger = logging.getLogger(__name__)


# ── Skill taxonomy ────────────────────────────────────────────────────────────

PYTHON_SKILLS = {
    "python", "fastapi", "flask", "django", "numpy", "pandas", "scipy",
    "matplotlib", "seaborn", "sqlalchemy", "pydantic", "celery",
}

AI_ML_CATEGORIES = {
    "deep_learning": {"pytorch", "tensorflow", "keras", "jax", "deep learning"},
    "nlp": {"nlp", "natural language processing", "huggingface", "transformers",
             "bert", "gpt", "llm", "spacy", "nltk", "text classification"},
    "computer_vision": {"computer vision", "opencv", "yolo", "resnet", "cnn",
                        "image recognition", "object detection"},
    "classical_ml": {"scikit-learn", "sklearn", "xgboost", "lightgbm", "catboost",
                     "random forest", "gradient boosting", "svm"},
    "mlops": {"mlflow", "kubeflow", "airflow", "wandb", "dvc", "bentoml",
              "triton", "torchserve", "docker", "kubernetes"},
    "data_engineering": {"spark", "kafka", "airflow", "dbt", "hadoop",
                         "databricks", "bigquery", "redshift"},
    "generative_ai": {"llm", "langchain", "llamaindex", "openai", "gemini",
                      "stable diffusion", "diffusion", "rag", "generative ai"},
}

VECTOR_DB_SKILLS = {
    "pinecone", "weaviate", "chromadb", "qdrant", "faiss",
    "milvus", "vespa", "opensearch", "pgvector",
}

RETRIEVAL_SKILLS = {
    "rag", "retrieval", "elasticsearch", "opensearch", "bm25",
    "dense retrieval", "hybrid search", "semantic search",
}

RANKING_SKILLS = {
    "ranking", "reranking", "recommendation", "ltr", "learning to rank",
    "collaborative filtering", "matrix factorization", "recommender",
}

EVALUATION_SKILLS = {
    "a/b testing", "ab testing", "model evaluation", "ndcg", "mrr", "map",
    "precision", "recall", "f1", "auc", "roc", "metrics", "experimentation",
}

PRODUCTION_AI_KEYWORDS = {
    "production", "deployed", "serving", "inference", "latency", "throughput",
    "real-time", "real time", "api", "microservice", "scaled", "million users",
}

CLOUD_PLATFORMS = {
    "aws", "amazon web services", "gcp", "google cloud", "azure",
    "microsoft azure", "google cloud platform",
}

AI_CERTIFICATIONS = {
    "aws machine learning", "aws certified machine learning",
    "google cloud professional ml", "tensorflow developer",
    "deeplearning.ai", "deep learning specialization",
    "machine learning specialization", "coursera ml",
    "azure ai engineer", "databricks certified",
}

ELITE_INSTITUTIONS = {
    "iit bombay", "iit delhi", "iit madras", "iit kanpur", "iit kharagpur",
    "iit roorkee", "iit guwahati", "iit hyderabad",
    "bits pilani", "bits goa", "bits hyderabad",
    "nit trichy", "nit surathkal", "nit warangal",
    "iisc", "iiit hyderabad", "iiit bangalore",
    "stanford", "mit", "carnegie mellon", "cmu", "berkeley", "oxford", "cambridge",
    "thapar", "vit", "manipal",
}

STEM_FIELDS = {
    "computer science", "computer engineering", "information technology",
    "electrical engineering", "electronics", "mathematics", "statistics",
    "data science", "artificial intelligence", "machine learning",
    "information science", "software engineering", "it",
}

SENIORITY_MAP = {
    "intern": 0, "trainee": 0,
    "junior": 1, "associate": 1, "entry": 1,
    "engineer": 2, "developer": 2, "analyst": 2, "scientist": 2,
    "senior": 3, "sr": 3, "lead": 4, "staff": 4,
    "principal": 5, "architect": 5, "manager": 4,
    "director": 6, "vp": 7, "head": 6, "cto": 8, "ceo": 8,
}

ENTERPRISE_SIGNALS = {
    "google", "microsoft", "amazon", "meta", "apple", "netflix", "uber",
    "flipkart", "swiggy", "zomato", "paytm", "razorpay", "infosys",
    "tcs", "wipro", "accenture", "deloitte", "ibm", "oracle", "salesforce",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _text_contains_any(text: str, keywords: set) -> bool:
    """Return True if any keyword appears in the lowercased text."""
    t = text.lower()
    return any(kw in t for kw in keywords)


def _get_title_seniority(title: Optional[str]) -> int:
    """Map a job title to a seniority integer."""
    if not title:
        return 0
    t = title.lower()
    best = 0
    for keyword, level in SENIORITY_MAP.items():
        if keyword in t:
            best = max(best, level)
    return best


def _experience_text(exp: Experience) -> str:
    """Combine title and description into one searchable string."""
    return f"{exp.title or ''} {exp.description or ''}".lower()


# ── Technical Intelligence ────────────────────────────────────────────────────

def _extract_technical(candidate: Candidate) -> TechnicalIntelligence:
    ti = TechnicalIntelligence()
    skills = set(s.lower() for s in candidate.skills.all_skills)

    # Combined text from all experience descriptions
    all_exp_text = " ".join(_experience_text(e) for e in candidate.experience)

    # Python depth
    python_hits = skills & PYTHON_SKILLS
    ti.python_adjacent_skills = sorted(python_hits)
    ti.python_depth = len(python_hits)

    # AI/ML depth by category
    ai_cats = []
    for category, keywords in AI_ML_CATEGORIES.items():
        if skills & keywords or _text_contains_any(all_exp_text, keywords):
            ai_cats.append(category)
    ti.ai_skill_categories = ai_cats
    ti.ai_ml_depth = len(ai_cats)

    # Boolean signals
    ti.has_vector_db = bool(skills & VECTOR_DB_SKILLS or
                            _text_contains_any(all_exp_text, VECTOR_DB_SKILLS))
    ti.has_retrieval = bool(skills & RETRIEVAL_SKILLS or
                            _text_contains_any(all_exp_text, RETRIEVAL_SKILLS))
    ti.has_ranking = bool(skills & RANKING_SKILLS or
                          _text_contains_any(all_exp_text, RANKING_SKILLS))
    ti.has_evaluation = bool(skills & EVALUATION_SKILLS or
                             _text_contains_any(all_exp_text, EVALUATION_SKILLS))
    ti.has_production_ai = _text_contains_any(all_exp_text, PRODUCTION_AI_KEYWORDS)
    ti.has_mlops = bool(skills & AI_ML_CATEGORIES["mlops"] or
                        _text_contains_any(all_exp_text, AI_ML_CATEGORIES["mlops"]))

    # Cloud and skill counts
    ti.cloud_platforms = len([p for p in CLOUD_PLATFORMS if p in skills])
    ti.skill_count = len(skills)

    # Skill diversity: number of non-empty AI categories + other tech buckets
    ti.skill_diversity = len(ai_cats) + (1 if ti.python_depth > 0 else 0) + \
                         (1 if ti.cloud_platforms > 0 else 0)

    return ti


# ── Career Intelligence ───────────────────────────────────────────────────────

def _extract_career(candidate: Candidate) -> CareerIntelligence:
    ci = CareerIntelligence()
    exps = candidate.experience

    if not exps:
        return ci

    # Durations
    durations = []
    for exp in exps:
        end = exp.end_date if exp.end_date else "present"
        m = duration_in_months(exp.start_date, end)
        if m is not None:
            durations.append(m)

    ci.number_of_roles = len(exps)
    ci.number_of_companies = len(set(
        normalize_company(e.company) for e in exps if e.company
    ))

    if durations:
        ci.total_experience_years = round(sum(durations) / 12, 1)
        ci.average_tenure_months = round(sum(durations) / len(durations), 1)
        ci.longest_tenure_months = max(durations)
        ci.shortest_tenure_months = min(durations)
        short_stints = sum(1 for d in durations if d < 12)
        ci.job_hopping_rate = round(short_stints / len(durations), 2)
        ci.job_hopping_flag = ci.job_hopping_rate > 0.5

    # AI experience years
    ai_months = 0
    for exp in exps:
        text = _experience_text(exp)
        if any(kw in text for cat in AI_ML_CATEGORIES.values() for kw in cat):
            end = exp.end_date if exp.end_date else "present"
            m = duration_in_months(exp.start_date, end)
            if m:
                ai_months += m
    ci.ai_experience_years = round(ai_months / 12, 1)

    # Title progression (chronological)
    dated = [(e, parse_date(e.start_date)) for e in exps]
    dated = sorted(
        [(e, d) for e, d in dated if d is not None],
        key=lambda x: x[1]
    )
    ci.title_progression = [normalize_title(e.title) for e, _ in dated if e.title]

    # Career growth rate: seniority delta / years
    if len(dated) >= 2:
        first_seniority = _get_title_seniority(dated[0][0].title)
        last_seniority = _get_title_seniority(dated[-1][0].title)
        years_span = ci.total_experience_years or 1
        ci.career_growth_rate = round(
            (last_seniority - first_seniority) / years_span, 2
        )

    # Seniority level of current/latest role
    latest_title = ci.title_progression[-1] if ci.title_progression else None
    ci.current_title_normalized = latest_title
    ci.seniority_level = _seniority_label(_get_title_seniority(latest_title))

    # Current employment
    for exp in exps:
        if exp.is_current:
            ci.is_currently_employed = True
            ci.current_company_normalized = normalize_company(exp.company)
            break

    # Days since last role (if not employed)
    if not ci.is_currently_employed:
        end_dates = [parse_date(e.end_date) for e in exps if e.end_date]
        end_dates = [d for d in end_dates if d]
        if end_dates:
            latest = max(end_dates)
            ci.days_since_last_role = (datetime.now() - latest).days

    # Company diversity (distinct industries)
    industries = [e.industry for e in exps if e.industry]
    ci.company_diversity = len(set(industries))

    # Startup ratio
    enterprise_count = sum(
        1 for e in exps
        if normalize_company(e.company) in ENTERPRISE_SIGNALS
    )
    ci.startup_ratio = round(
        1 - (enterprise_count / ci.number_of_roles), 2
    ) if ci.number_of_roles else 0.0

    return ci


def _seniority_label(level: int) -> str:
    if level <= 0:
        return "intern"
    if level == 1:
        return "junior"
    if level == 2:
        return "mid"
    if level in (3, 4):
        return "senior"
    if level == 5:
        return "principal"
    return "executive"


# ── Education Intelligence ────────────────────────────────────────────────────

DEGREE_TIER = {
    "phd": 5, "doctorate": 5,
    "m.tech": 4, "mtech": 4, "m.s": 4, "ms": 4,
    "mba": 4, "masters": 4, "m.e": 4, "me": 4,
    "b.tech": 3, "btech": 3, "b.e": 3, "be": 3,
    "b.s": 3, "bs": 3, "bachelors": 3,
    "diploma": 2, "12th": 1, "high school": 1,
}


def _extract_education(candidate: Candidate) -> EducationIntelligence:
    ei = EducationIntelligence()
    edu_list = candidate.education

    if not edu_list:
        return ei

    tiers = []
    for edu in edu_list:
        degree = (edu.degree or "").lower().strip()
        tier = DEGREE_TIER.get(degree, 0)
        tiers.append(tier)

        if edu.institution:
            ei.institutions.append(edu.institution)
            if edu.institution.lower() in ELITE_INSTITUTIONS:
                ei.is_elite_institution = True

        if edu.field_of_study:
            ei.fields_of_study.append(edu.field_of_study)
            if edu.field_of_study.lower() in STEM_FIELDS:
                ei.is_stem = True
            if any(kw in edu.field_of_study.lower()
                   for kw in {"artificial intelligence", "machine learning", "data science"}):
                ei.education_ai_focus = True

    if tiers:
        ei.degree_tier = max(tiers)
    ei.highest_degree = max(
        edu_list,
        key=lambda e: DEGREE_TIER.get((e.degree or "").lower().strip(), 0),
        default=None
    )
    ei.highest_degree = ei.highest_degree.degree if ei.highest_degree else None
    ei.has_postgrad = ei.degree_tier >= 4

    return ei


# ── Behavior Intelligence ─────────────────────────────────────────────────────

def _extract_behavior(candidate: Candidate) -> BehaviorIntelligence:
    bi = BehaviorIntelligence()
    r = candidate.redrob

    bi.has_github = bool(r.github_url)
    bi.has_portfolio = bool(r.portfolio_url)
    bi.has_linkedin = bool(r.linkedin_url)
    bi.is_open_to_work = bool(r.is_open_to_work)
    bi.notice_period_days = r.notice_period_days
    bi.last_active_days = r.last_active_days
    bi.response_rate = r.response_rate

    bi.certification_count = len(candidate.certifications)
    ai_certs = []
    for cert in candidate.certifications:
        name = (cert.name or "").lower()
        if any(ac in name for ac in AI_CERTIFICATIONS):
            ai_certs.append(cert.name)
    bi.has_ai_certifications = len(ai_certs) > 0
    bi.ai_certification_names = ai_certs

    bi.language_count = len(candidate.languages)
    bi.multilingual = bi.language_count > 1

    # Profile completeness
    checks = [
        bool(candidate.profile.name),
        bool(candidate.profile.email),
        bool(candidate.profile.current_title),
        bool(candidate.profile.location),
        bool(candidate.profile.summary),
        bool(candidate.experience),
        bool(candidate.education),
        bool(candidate.skills.all_skills),
        bool(r.linkedin_url),
        bool(r.github_url or r.portfolio_url),
    ]
    bi.profile_completeness = round(sum(checks) / len(checks), 2)

    return bi


# ── Risk Intelligence ─────────────────────────────────────────────────────────

def _extract_risk(candidate: Candidate, career: CareerIntelligence) -> RiskIntelligence:
    ri = RiskIntelligence()
    exps = candidate.experience

    # Parse all dates for timeline analysis
    timeline = []
    missing_dates = 0
    for exp in exps:
        start = parse_date(exp.start_date)
        end = parse_date(exp.end_date) if exp.end_date else (
            datetime.now() if exp.is_current else None
        )
        if start is None or (end is None and not exp.is_current):
            missing_dates += 1
        if start and end:
            timeline.append((start, end, exp.title))

    ri.missing_dates_ratio = round(
        missing_dates / len(exps), 2
    ) if exps else 0.0

    # Sort by start date
    timeline.sort(key=lambda x: x[0])

    # Gap detection (> 6 months between roles)
    max_gap = 0
    for i in range(1, len(timeline)):
        prev_end = timeline[i - 1][1]
        curr_start = timeline[i][0]
        if curr_start > prev_end:
            gap_months = (curr_start.year - prev_end.year) * 12 + \
                         (curr_start.month - prev_end.month)
            max_gap = max(max_gap, gap_months)

    ri.has_timeline_gaps = max_gap > 6
    ri.timeline_gap_months = max_gap

    # Overlap detection
    overlap_count = 0
    for i in range(1, len(timeline)):
        prev_end = timeline[i - 1][1]
        curr_start = timeline[i][0]
        if curr_start < prev_end:
            overlap_count += 1
    ri.has_timeline_overlap = overlap_count > 0
    ri.overlap_count = overlap_count

    # Job hopping flag (from career)
    ri.job_hopping_flag = career.job_hopping_rate > 0.5

    # Skill inflation: >40 skills with <2 years experience
    skill_count = len(candidate.skills.all_skills)
    ri.skill_inflation_flag = (
        skill_count > 40 and career.total_experience_years < 2
    )
    ri.suspicious_skill_count = (
    skill_count >= 40
    and career.total_experience_years < 1
)

    # Short descriptions ratio
    desc_lengths = [
        len(e.description or "") for e in exps
    ]
    if desc_lengths:
        short = sum(1 for d in desc_lengths if d < 50)
        ri.short_descriptions_ratio = round(short / len(desc_lengths), 2)

    # Total risk flag count
    ri.risk_flag_count = sum([
        ri.has_timeline_gaps,
        ri.has_timeline_overlap,
        ri.job_hopping_flag,
        ri.skill_inflation_flag,
        ri.suspicious_skill_count,
        ri.missing_dates_ratio > 0.5,
        ri.short_descriptions_ratio > 0.5,
    ])

    return ri


# ── Main entry point ──────────────────────────────────────────────────────────

def extract_intelligence(candidate: Candidate) -> CandidateIntelligence:
    """
    Transform a Candidate into a CandidateIntelligence object.

    Args:
        candidate: Parsed Candidate instance.

    Returns:
        CandidateIntelligence with all dimensions populated.
    """
    technical = _extract_technical(candidate)
    career = _extract_career(candidate)
    education = _extract_education(candidate)
    behavior = _extract_behavior(candidate)
    risk = _extract_risk(candidate, career)

    return CandidateIntelligence(
        candidate_id=candidate.profile.candidate_id,
        name=candidate.profile.name,
        technical=technical,
        career=career,
        education=education,
        behavior=behavior,
        risk=risk,
    )


def extract_intelligence_batch(
    candidates: list,
    log_every: int = 100,
) -> list:
    """
    Extract intelligence for a list of candidates.

    Args:
        candidates: List of Candidate instances.
        log_every: Log progress every N candidates.

    Returns:
        List of CandidateIntelligence instances.
    """
    results = []
    for i, candidate in enumerate(candidates, start=1):
        try:
            intel = extract_intelligence(candidate)
            results.append(intel)
        except Exception as e:
            logger.error(
                "Failed to extract intelligence for %s: %s",
                candidate.profile.candidate_id, e
            )
        if i % log_every == 0:
            logger.info("Intelligence extracted: %d / %d", i, len(candidates))

    logger.info("Intelligence extraction complete: %d candidates", len(results))
    return results
