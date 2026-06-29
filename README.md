# RedRank AI
### Hiring people, not keywords.

An intelligent candidate discovery and ranking system built for the Redrob AI Challenge.

---

## What makes RedRank different

Most resume matchers count keyword overlaps. RedRank evaluates:

- Semantic fit — meaning, not just words
- Career trajectory — growth signals, not just titles
- Behavioral signals — ownership, impact, leadership patterns
- Production experience — scale, complexity, real-world systems
- Explainability — every rank score has a human-readable reason

---

## Architecture

    redrank-ai/
    ├── src/
    │   ├── ingestion/       # Data loading and parsing
    │   ├── features/        # Feature extraction modules
    │   ├── ranking/         # Scoring and ranking logic
    │   ├── explainability/  # Human-readable explanations
    │   └── utils/           # Shared utilities
    ├── configs/             # All tunable parameters
    ├── data/                # Processed data (raw excluded)
    ├── models/              # Model cache (excluded from git)
    ├── outputs/             # Submission CSVs
    └── tests/               # Unit tests

---

## Constraints Met

- CPU only
- No external API calls during ranking
- Runtime under 5 minutes
- Memory under 16GB
- Top 100 candidates ranked
- Valid submission CSV
- Modular architecture
- Explainable ranking

---

## Setup

    git clone https://github.com/techAsmita/RedRank-AI.git
    cd RedRank-AI
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm

---

Built for Redrob AI — Intelligent Candidate Discovery and Ranking Challenge.
