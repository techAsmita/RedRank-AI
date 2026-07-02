# RedRank AI
### *Most hiring systems retrieve resumes. RedRank AI evaluates evidence, models recruiter intent, and explains every hiring decision.*

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![CPU Only](https://img.shields.io/badge/compute-CPU%20only-green.svg)]()
[![Runtime](https://img.shields.io/badge/runtime-116s%20%2F%20100K%20candidates-brightgreen.svg)]()
[![Submission](https://img.shields.io/badge/submission-valid-success.svg)]()

---

## The Problem

Every ATS on the market does the same thing: match keywords.

A candidate who lists "RAG", "Pinecone", and "LLM" in their skills section scores higher than a candidate who spent four years building production retrieval systems at a product company — because the first candidate used more keywords.

This is not hiring. This is CTRL+F at scale.

The Redrob challenge explicitly warns against this trap:

> *"The right answer is not find candidates whose skills section contains the most AI keywords. That is a trap we have explicitly built into the dataset."*

RedRank AI was designed from day one to avoid this trap — and to explain, for every candidate, exactly why they ranked where they did.

---

## Our Insight

A keyword is not evidence.

A keyword in a skill list, corroborated by job history, a GitHub presence, a relevant certification, and four years of AI/ML experience — that is evidence.

RedRank AI does not ask "does this resume contain the right words?"

It asks "what is the actual proof that this candidate can do this job?"

This distinction drives every architectural decision in the system.

---

## Pipeline

**Candidate** → **Intelligence** → **Evidence Graph** → **Job Intent** → **8 Decision Policies** → **Decision Fusion Engine** → **Top-100 Ranked Output**

Every step is deterministic, explainable, and CPU-only.

---

## Phases

### Phase 1 — Data Foundation
Streaming JSONL ingestion processes 100,000 candidates without loading the file into memory. Pydantic models match the real Redrob schema exactly, preserving rich skill signals (proficiency, endorsements, duration per skill) that flat keyword lists discard.

### Phase 2 — Candidate Intelligence
Every candidate is transformed into a `CandidateIntelligence` object with 40+ deterministic signals across five dimensions:

- **TechnicalIntelligence** — Python depth, AI/ML category coverage, vector DB presence, retrieval/ranking/evaluation evidence, production AI deployment signals
- **CareerIntelligence** — total and AI-specific experience, seniority level, career growth rate, job-hopping rate, company diversity, startup ratio
- **EducationIntelligence** — degree tier, STEM flag, elite institution detection, AI/ML focus
- **BehaviorIntelligence** — GitHub activity, certifications, platform engagement, notice period, response rate
- **RiskIntelligence** — timeline gaps, overlaps, skill inflation, suspicious skill counts, missing data ratios

### Phase 3 — Job Intent + Evidence Graph
A deterministic rule-based parser extracts structured recruiter intent from the JD — no LLM, no embeddings, fully reproducible. The result is a `JobIntent` object capturing explicit requirements, preferred skills, behavioral expectations, and disqualifiers.

An `EvidenceGraph` then connects each candidate's intelligence to each JD requirement, producing 19 `EvidenceNode` objects. Each node has a strength score (0.0–1.0), a confidence label (STRONG / MODERATE / WEAK / NONE), a list of source references, and a human-readable note. No claim is made without a traceable source.

### Phase 4 — Decision Policy Engine
Eight independent policies evaluate the candidate, each answering one recruiter question:

| Policy | Question |
|---|---|
| Technical Fit | Can this candidate technically perform the role? |
| Production Readiness | Has the candidate built and operated production systems? |
| Hiring Readiness | Can this candidate realistically be hired right now? |
| Career Trajectory | Does the career show healthy growth and stability? |
| Professional Signals | Does the profile demonstrate engineering maturity? |
| Evidence Strength | How trustworthy is the available evidence overall? |
| JD Intent Coverage | How well does the candidate satisfy recruiter intent (not keywords)? |
| Risk Assessment | What hiring risks exist for this candidate? |

Each policy returns PASS / PARTIAL / FAIL, a confidence score, supporting evidence, concerns, and a decision trace. Policies do not communicate with each other. No overall score is computed at this stage.

An `EvidenceValidator` audits every policy result and rejects any conclusion not backed by a traceable evidence reference.

### Phase 5 — Decision Fusion Engine
The fusion engine models how an experienced recruiter resolves conflicting signals:

**Hard Gates** (eliminate before scoring):
- Pure research background with no production deployment
- Keyword-only profiles with no corroborating career evidence
- Zero recruiter engagement combined with long platform inactivity

**Anchor Scoring** (sets rank tier):
- Tier score = minimum of Technical Fit, Production Readiness, JD Intent Coverage, Career Trajectory confidences
- Why minimum? A candidate who is mediocre in one anchor dimension should not be elevated by strength in another — this directly models the JD's "we'd rather see 10 great matches than 1000 maybes" philosophy

**Conflict Resolution** (5 named rules):
- Technical PASS + Hiring FAIL → demote one tier
- High risk + strong technical → 15% booster penalty
- Strong evidence + wrong domain → evidence strength capped
- Career PASS + Intent FAIL → demote one tier
- Production PASS + Evidence weak → tier score penalty

**Booster Scoring** (fine-grained ordering within tier):
- Hiring Readiness (25%), Professional Signals (20%), Evidence Strength (20%), Risk Assessment (20%), Career Growth (15%)

**Response Rate Multiplier**:
- Recruiter response rate acts as an independent score dampener — a perfect-on-paper candidate with 5% response rate is genuinely deprioritized, matching the JD's explicit instruction

**Final fusion score**: `(tier_score * 0.70 + booster_score * 0.30) * response_multiplier`

---

## Results

| Metric | Value |
|---|---|
| Candidates processed | 100,000 |
| Runtime | 116.7 seconds |
| Memory | Well within 16GB |
| Skipped / errored | 0 |
| Gate failures (filtered) | 33,075 |
| Tier 1 candidates | 106 |
| Tier 2 candidates | 11,549 |
| Submission validation | PASSED |
| External API calls | 0 |
| GPU required | No |

---

## What Makes RedRank Different

Most submissions will use embeddings and cosine similarity. RedRank AI uses none of these.

Instead:

- Every skill is weighted by proof — job history, duration, endorsements, certifications — not just presence in a skills list
- Every ranking decision is traceable to a specific evidence source
- The system explicitly models the keyword-trap the challenge warns against, and penalizes it
- Recruiter behavioral signals (response rate, platform activity, notice period) are first-class signals, not afterthoughts
- Every candidate in the top-100 has a human-readable explanation of exactly why they ranked there

---

## How to Run

```bash
git clone https://github.com/techAsmita/RedRank-AI.git
cd RedRank-AI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

python3 main.py \
  --candidates ./candidates.jsonl \
  --jd ./job_description.docx \
  --output ./outputs/agent_x.csv
```

Validate submission:
```bash
python3 validate_submission.py outputs/agent_x.csv
```

---

## Project Structure

redrank-ai/
├── main.py                        # Single entry point
├── src/
│   ├── ingestion/                 # Phase 1 — Data Foundation
│   │   ├── loader.py              # Streaming JSONL
│   │   ├── models.py              # Pydantic candidate models
│   │   └── parser.py              # Raw JSON → Candidate objects
│   ├── features/                  # Phase 2 — Intelligence
│   │   ├── intelligence_models.py # CandidateIntelligence dataclasses
│   │   ├── intelligence_extractor.py
│   │   └── preprocessing.py
│   ├── job_intelligence/          # Phase 3 — Job Intent
│   │   ├── models.py
│   │   ├── parser.py
│   │   ├── extractor.py
│   │   ├── taxonomy.py
│   │   └── patterns.py
│   ├── evidence/                  # Phase 3 — Evidence Graph
│   │   ├── models.py
│   │   ├── extractor.py
│   │   └── printer.py
│   ├── decision/                  # Phase 4 — Decision Policies
│   │   ├── policies/
│   │   │   ├── technical_fit.py
│   │   │   ├── production_readiness.py
│   │   │   ├── hiring_readiness.py
│   │   │   ├── career_trajectory.py
│   │   │   ├── professional_signals.py
│   │   │   ├── evidence_strength.py
│   │   │   ├── jd_intent_coverage.py
│   │   │   └── risk_assessment.py
│   │   ├── evaluator.py
│   │   ├── validator.py
│   │   └── explanation.py
│   └── fusion/                    # Phase 5 — Decision Fusion
│       ├── engine.py              # DecisionFusionEngine
│       ├── gates.py               # Hard gate evaluator
│       ├── aggregator.py          # Anchor + booster scoring
│       ├── resolver.py            # Conflict resolution
│       ├── ranker.py              # Top-100 generator
│       └── reasoning.py          # Per-candidate reasoning
├── configs/
│   └── settings.yaml
├── outputs/
│   └── agent_x.csv               # Final submission
└── tests/                        # 25+ tests across all phases

---

## Team

**Team Agent X**
Built for the Redrob AI Intelligent Candidate Discovery and Ranking Challenge.

*Hiring people, not keywords.*
