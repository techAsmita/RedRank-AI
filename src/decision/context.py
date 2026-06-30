from __future__ import annotations

from dataclasses import dataclass

from src.features.intelligence_models import CandidateIntelligence
from src.job_intelligence.models import JobIntent
from src.evidence.models import EvidenceGraph


@dataclass
class DecisionContext:
    """
    Single object passed into every policy.

    Bundles everything a policy might need:
    - candidate_intelligence: who the candidate is
    - job_intent: what the recruiter wants
    - evidence_graph: proof connecting the two

    Policies read from this context only. They never reach
    into raw Candidate or JD objects directly.
    """
    candidate_intelligence: CandidateIntelligence
    job_intent: JobIntent
    evidence_graph: EvidenceGraph
