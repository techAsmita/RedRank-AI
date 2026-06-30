from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ── Evidence strength constants ───────────────────────────────────────────────

STRONG   = "STRONG"
MODERATE = "MODERATE"
WEAK     = "WEAK"
NONE     = "NONE"


@dataclass
class EvidenceSource:
    """
    A single piece of evidence supporting a requirement.

    Every claim must point to a source.
    """
    source_type: str              # "skill" | "experience" | "certification" | "behavior"
    value: str                    # The actual evidence value
    months: Optional[int] = None  # Duration if applicable


@dataclass
class EvidenceNode:
    """
    Evidence for a single JD requirement.

    Not binary. Not a score.
    A structured answer to: does the candidate satisfy this requirement?
    """
    requirement: str                                        # What the JD asks for
    satisfied: bool = False                                 # Is it met?
    confidence: str = NONE                                  # STRONG / MODERATE / WEAK / NONE
    strength: float = 0.0                                   # 0.0 to 1.0
    sources: list = field(default_factory=list)             # List[EvidenceSource]
    notes: str = ""                                         # Human-readable explanation


@dataclass
class EvidenceGraph:
    """
    Complete evidence profile for one candidate against one JD.

    This is the input to Phase 4 scoring.
    Every score in Phase 4 will be derived from this graph.
    No scores are stored here — only evidence.
    """
    candidate_id: Optional[str] = None
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None

    # Technical evidence
    python:             EvidenceNode = field(default_factory=lambda: EvidenceNode("Python"))
    retrieval:          EvidenceNode = field(default_factory=lambda: EvidenceNode("Retrieval"))
    evaluation:         EvidenceNode = field(default_factory=lambda: EvidenceNode("Evaluation"))
    mlops:              EvidenceNode = field(default_factory=lambda: EvidenceNode("MLOps"))
    cloud:              EvidenceNode = field(default_factory=lambda: EvidenceNode("Cloud"))
    production_ai:      EvidenceNode = field(default_factory=lambda: EvidenceNode("Production AI"))
    vector_db:          EvidenceNode = field(default_factory=lambda: EvidenceNode("Vector DB"))
    ranking:            EvidenceNode = field(default_factory=lambda: EvidenceNode("Ranking"))

    # Career evidence
    experience_years:   EvidenceNode = field(default_factory=lambda: EvidenceNode("Experience Years"))
    seniority:          EvidenceNode = field(default_factory=lambda: EvidenceNode("Seniority"))
    career_growth:      EvidenceNode = field(default_factory=lambda: EvidenceNode("Career Growth"))
    ai_experience:      EvidenceNode = field(default_factory=lambda: EvidenceNode("AI Experience"))

    # Education evidence
    education:          EvidenceNode = field(default_factory=lambda: EvidenceNode("Education"))

    # Behavior evidence
    github_presence:    EvidenceNode = field(default_factory=lambda: EvidenceNode("GitHub Presence"))
    certifications:     EvidenceNode = field(default_factory=lambda: EvidenceNode("Certifications"))
    availability:       EvidenceNode = field(default_factory=lambda: EvidenceNode("Availability"))
    profile_quality:    EvidenceNode = field(default_factory=lambda: EvidenceNode("Profile Quality"))

    # Risk
    risk_flags:         EvidenceNode = field(default_factory=lambda: EvidenceNode("Risk Flags"))
