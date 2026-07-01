"""
main.py
--------
RedRank AI — Full Pipeline Entry Point.

Runs the complete candidate ranking pipeline:

  candidates.jsonl
        │
        ▼
  Streaming Ingestion (Phase 1)
        │
        ▼
  Candidate Intelligence (Phase 2)
        │
        ▼
  Evidence Graph (Phase 3)
        │
        ▼
  Job Intent (Phase 3)
        │
        ▼
  Decision Policy Engine (Phase 4)
        │
        ▼
  Decision Fusion Engine (Phase 5)
        │
        ▼
  Top-100 Ranking
        │
        ▼
  submission.csv

Constraints:
- CPU only
- No external API calls
- Runtime < 5 minutes
- Memory < 16GB
- Top 100 candidates ranked
"""

from __future__ import annotations

import csv
import logging
import os
import time
from pathlib import Path
from typing import Optional

from src.ingestion.loader import stream_jsonl, load_config
from src.ingestion.parser import parse_candidate
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

from src.fusion.engine import DecisionFusionEngine
from src.fusion.ranker import rank_candidates, print_ranking_summary
from src.fusion.reasoning import generate_reasoning
from src.fusion.models import FusionScore


# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ── Paths ─────────────────────────────────────────────────────────────────────

CANDIDATES_PATH = Path(
    os.environ.get(
        "CANDIDATES_PATH",
        "/Users/asmaniroy/Downloads/[PUB] India_runs_data_and_ai_challenge/"
        "India_runs_data_and_ai_challenge/candidates.jsonl"
    )
)

JD_PATH = Path(
    os.environ.get(
        "JD_PATH",
        "/Users/asmaniroy/Downloads/[PUB] India_runs_data_and_ai_challenge/"
        "India_runs_data_and_ai_challenge/job_description.docx"
    )
)

OUTPUT_PATH = Path(
    os.environ.get("OUTPUT_PATH", "outputs/submission.csv")
)

TOP_N = int(os.environ.get("TOP_N", "100"))
LOG_EVERY = int(os.environ.get("LOG_EVERY", "1000"))


# ── Policy factory ────────────────────────────────────────────────────────────

def _build_policies():
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


# ── CSV writer ────────────────────────────────────────────────────────────────

def write_submission_csv(
    ranked_candidates: list,
    intelligence_map: dict,
    policy_results_map: dict,
    output_path: Path,
) -> None:
    """
    Write the final submission CSV.

    Columns based on competition submission spec:
    rank, candidate_id, score, reasoning
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        for score in ranked_candidates:
            intel = intelligence_map.get(score.candidate_id)
            policy_results = policy_results_map.get(score.candidate_id, [])

            reasoning_text = score.reasoning
            if intel and policy_results:
                try:
                    reasoning = generate_reasoning(score, intel, policy_results)
                    reasoning_text = reasoning.overall_verdict
                except Exception as e:
                    logger.warning(
                        "Reasoning generation failed for %s: %s",
                        score.candidate_id, e
                    )

            writer.writerow([
                score.candidate_id,
                score.rank,
                round(score.fusion_score, 6),
                reasoning_text,
            ])

    logger.info("Submission CSV written to %s", output_path)


# ── JD loader ─────────────────────────────────────────────────────────────────

def _load_jd(jd_path: Path) -> str:
    """Load JD from docx or markdown depending on extension."""
    if jd_path.suffix == ".docx":
        try:
            from docx import Document
            doc = Document(str(jd_path))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            logger.warning("Failed to load docx JD: %s — falling back to md", e)

    # Fallback to synthetic JD
    fallback = Path("data/sample/job_description.md")
    logger.warning("Using fallback JD: %s", fallback)
    return load_job_description(fallback)


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(
    candidates_path: Path = CANDIDATES_PATH,
    jd_path: Path = JD_PATH,
    output_path: Path = OUTPUT_PATH,
    top_n: int = TOP_N,
    log_every: int = LOG_EVERY,
    max_candidates: Optional[int] = None,  # for testing — None = process all
) -> None:
    """
    Run the complete RedRank AI pipeline.

    Memory strategy: process candidates one at a time (streaming),
    keep only intelligence + scores in memory (not raw records).
    This keeps memory well within 16GB even for 100K+ candidates.
    """
    start_time = time.time()
    logger.info("RedRank AI pipeline starting")
    logger.info("Candidates: %s", candidates_path)
    logger.info("JD: %s", jd_path)
    logger.info("Output: %s", output_path)

    # Step 1: Load Job Intent
    logger.info("Loading job description...")
    jd_text = _load_jd(jd_path)
    job_intent = parse_job_description(jd_text)
    logger.info("Job Intent extracted: %s", job_intent.metadata.title)

    # Step 2: Initialize pipeline components
    evaluator = DecisionEvaluator(_build_policies())
    fusion_engine = DecisionFusionEngine()

    # Step 3: Stream candidates and process one at a time
    intelligence_map = {}
    policy_results_map = {}
    fusion_scores = []

    processed = 0
    skipped = 0

    logger.info("Streaming candidates from %s...", candidates_path)

    for raw in stream_jsonl(candidates_path, log_every=log_every):
        if max_candidates and processed >= max_candidates:
            break

        # Parse
        candidate = parse_candidate(raw)
        if candidate is None:
            skipped += 1
            continue

        # Intelligence
        try:
            intel = extract_intelligence(candidate)
        except Exception as e:
            logger.warning("Intelligence extraction failed: %s", e)
            skipped += 1
            continue

        # Evidence Graph
        try:
            evidence_graph = build_evidence_graph(intel, job_intent)
        except Exception as e:
            logger.warning(
                "Evidence graph failed for %s: %s",
                intel.candidate_id, e
            )
            skipped += 1
            continue

        # Decision Policies
        try:
            context = DecisionContext(
                candidate_intelligence=intel,
                job_intent=job_intent,
                evidence_graph=evidence_graph,
            )
            summary = evaluator.evaluate(context)
        except Exception as e:
            logger.warning(
                "Policy evaluation failed for %s: %s",
                intel.candidate_id, e
            )
            skipped += 1
            continue

        # Fusion
        try:
            score = fusion_engine.fuse(
                intel, summary.policy_results, job_intent
            )
        except Exception as e:
            logger.warning(
                "Fusion failed for %s: %s",
                intel.candidate_id, e
            )
            skipped += 1
            continue

        # Store — intelligence and policy results kept in memory
        # for reasoning generation after ranking
        intelligence_map[intel.candidate_id] = intel
        policy_results_map[intel.candidate_id] = summary.policy_results
        fusion_scores.append(score)
        processed += 1

        if processed % log_every == 0:
            elapsed = time.time() - start_time
            logger.info(
                "Progress: %d processed, %d skipped | %.1fs elapsed",
                processed, skipped, elapsed,
            )

    logger.info(
        "Processing complete: %d candidates, %d skipped",
        processed, skipped,
    )

    # Step 4: Rank
    logger.info("Ranking %d candidates...", len(fusion_scores))
    intelligence_list = list(intelligence_map.values())
    output = rank_candidates(fusion_scores, intelligence_list, top_n=top_n)
    print_ranking_summary(output)

    # Step 5: Write submission CSV
    write_submission_csv(
        ranked_candidates=output.ranked_candidates,
        intelligence_map=intelligence_map,
        policy_results_map=policy_results_map,
        output_path=output_path,
    )

    elapsed = time.time() - start_time
    logger.info(
        "Pipeline complete in %.1fs | Top %d written to %s",
        elapsed, top_n, output_path,
    )

    if elapsed > 300:
        logger.warning(
            "Runtime %.1fs exceeds 5-minute competition constraint!", elapsed
        )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RedRank AI ranking pipeline")
    parser.add_argument(
        "--candidates", type=str, default=str(CANDIDATES_PATH),
        help="Path to candidates.jsonl"
    )
    parser.add_argument(
        "--jd", type=str, default=str(JD_PATH),
        help="Path to job_description.docx or .md"
    )
    parser.add_argument(
        "--output", type=str, default=str(OUTPUT_PATH),
        help="Path for submission CSV output"
    )
    parser.add_argument(
        "--top-n", type=int, default=TOP_N,
        help="Number of candidates to rank (default 100)"
    )
    parser.add_argument(
        "--max-candidates", type=int, default=None,
        help="Limit candidates processed (for testing)"
    )
    parser.add_argument(
        "--log-every", type=int, default=LOG_EVERY,
        help="Log progress every N candidates"
    )

    args = parser.parse_args()

    run_pipeline(
        candidates_path=Path(args.candidates),
        jd_path=Path(args.jd),
        output_path=Path(args.output),
        top_n=args.top_n,
        max_candidates=args.max_candidates,
        log_every=args.log_every,
    )
