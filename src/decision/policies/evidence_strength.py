"""
evidence_strength.py
----------------------
Evidence Strength policy.

Question: How trustworthy is the available evidence supporting
this candidate's profile overall?

Unlike other policies, this one looks across every node in the
Evidence Graph and judges aggregate evidence quality — a meta-policy
on the reliability of the conclusions, not the conclusions themselves.
"""

from __future__ import annotations

from src.decision.context import DecisionContext
from src.decision.interfaces import DecisionPolicyInterface
from src.decision.models import (
    DecisionEvidence,
    DecisionPolicy,
    DecisionTrace,
    PolicyResult,
    PolicyStatus,
)
from src.evidence.models import STRONG, MODERATE, WEAK, NONE


class EvidenceStrengthPolicy(DecisionPolicyInterface):

    @property
    def policy(self) -> DecisionPolicy:
        return DecisionPolicy(
            id="evidence_strength",
            name="Evidence Strength",
            description="Evaluates the overall trustworthiness of evidence backing the candidate profile.",
        )

    def evaluate(self, context: DecisionContext) -> PolicyResult:
        graph = context.evidence_graph

        evidence = []
        concerns = []
        trace = []

        all_nodes = [
            ("Python", graph.python),
            ("Retrieval", graph.retrieval),
            ("Evaluation", graph.evaluation),
            ("MLOps", graph.mlops),
            ("Cloud", graph.cloud),
            ("Production AI", graph.production_ai),
            ("Vector DB", graph.vector_db),
            ("Ranking", graph.ranking),
            ("Experience Years", graph.experience_years),
            ("Seniority", graph.seniority),
            ("Career Growth", graph.career_growth),
            ("AI Experience", graph.ai_experience),
            ("Education", graph.education),
            ("GitHub", graph.github_presence),
            ("Certifications", graph.certifications),
            ("Availability", graph.availability),
            ("Profile Quality", graph.profile_quality),
        ]

        strong_count = sum(1 for _, n in all_nodes if n.confidence == STRONG)
        moderate_count = sum(1 for _, n in all_nodes if n.confidence == MODERATE)
        weak_count = sum(1 for _, n in all_nodes if n.confidence == WEAK)
        none_count = sum(1 for _, n in all_nodes if n.confidence == NONE)

        total = len(all_nodes)
        total_sources = sum(len(n.sources) for _, n in all_nodes)

        trace.append(DecisionTrace(
            step="Evidence Distribution",
            observation=f"STRONG={strong_count} MODERATE={moderate_count} WEAK={weak_count} NONE={none_count}",
            outcome=f"{total_sources} total evidence sources across {total} dimensions",
        ))

        confidence = round(
            (strong_count * 1.0 + moderate_count * 0.5 + weak_count * 0.25) / total,
            2,
        )

        if strong_count >= total * 0.4:
            evidence.append(DecisionEvidence(
                source="Evidence Graph",
                field="Strong Evidence Coverage",
                value=f"{strong_count}/{total}",
                explanation=f"{strong_count} of {total} dimensions have strong, multi-source evidence.",
            ))

        if none_count >= total * 0.4:
            concerns.append(DecisionEvidence(
                source="Evidence Graph",
                field="Missing Evidence",
                value=f"{none_count}/{total}",
                explanation=f"{none_count} of {total} dimensions have no supporting evidence at all.",
            ))

        if total_sources < total:
            concerns.append(DecisionEvidence(
                source="Evidence Graph",
                field="Source Density",
                value=f"{total_sources} sources / {total} dimensions",
                explanation="Average less than one evidence source per dimension — conclusions may be thin.",
            ))

        # Always surface the aggregate distribution as evidence, even when
        # neither the strong-coverage nor missing-evidence thresholds are hit.
        # This guarantees every conclusion is traceable to a referenced fact.
        if not evidence and not concerns:
            evidence.append(DecisionEvidence(
                source="Evidence Graph",
                field="Evidence Distribution",
                value=f"STRONG={strong_count} MODERATE={moderate_count} WEAK={weak_count} NONE={none_count}",
                explanation=f"Mixed evidence quality across {total} dimensions with {total_sources} total sources; no dominant pattern in either direction.",
            ))

        if confidence >= 0.65:
            status = PolicyStatus.PASS
        elif confidence >= 0.35:
            status = PolicyStatus.PARTIAL
        else:
            status = PolicyStatus.FAIL

        return PolicyResult(
            policy_name=self.policy.name,
            status=status,
            confidence=confidence,
            supporting_evidence=evidence,
            concerns=concerns,
            decision_trace=trace,
        )
