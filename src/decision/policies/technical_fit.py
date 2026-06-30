"""
technical_fit.py
-----------------
Technical Fit policy.

Question: Can this candidate technically perform this role?

Reads strength/confidence directly from the EvidenceGraph,
which already aggregated skills, experience duration, and
description evidence for each technical dimension.
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
from src.evidence.models import STRONG, MODERATE


class TechnicalFitPolicy(DecisionPolicyInterface):

    @property
    def policy(self) -> DecisionPolicy:
        return DecisionPolicy(
            id="technical_fit",
            name="Technical Fit",
            description="Evaluates whether the candidate can technically perform the role.",
        )

    def evaluate(self, context: DecisionContext) -> PolicyResult:
        graph = context.evidence_graph
        job = context.job_intent.technical

        evidence = []
        concerns = []
        trace = []
        confidence = 0.0
        weight_total = 0.0

        # Only evaluate dimensions the JD actually requires
        dimensions = []
        if job.python_required:
            dimensions.append(("Python", graph.python, 0.30))
        if job.retrieval:
            dimensions.append(("Retrieval", graph.retrieval, 0.25))
        if job.evaluation:
            dimensions.append(("Evaluation", graph.evaluation, 0.15))
        if job.mlops:
            dimensions.append(("MLOps", graph.mlops, 0.15))
        if job.cloud_required:
            dimensions.append(("Cloud", graph.cloud, 0.15))

        # Fallback: if JD specifies nothing explicit, weigh core dimensions evenly
        if not dimensions:
            dimensions = [
                ("Python", graph.python, 0.25),
                ("Retrieval", graph.retrieval, 0.25),
                ("Production AI", graph.production_ai, 0.25),
                ("MLOps", graph.mlops, 0.25),
            ]

        for label, node, weight in dimensions:
            weight_total += weight
            confidence += node.strength * weight

            trace.append(DecisionTrace(
                step=label,
                observation=f"strength={node.strength:.2f}, confidence={node.confidence}",
                outcome="satisfied" if node.satisfied else "not satisfied",
            ))

            if node.satisfied and node.confidence in (STRONG, MODERATE):
                evidence.append(DecisionEvidence(
                    source="Evidence Graph",
                    field=label,
                    value=f"{node.strength:.2f}",
                    explanation=node.notes,
                ))
            elif not node.satisfied:
                concerns.append(DecisionEvidence(
                    source="Evidence Graph",
                    field=label,
                    value=f"{node.strength:.2f}",
                    explanation=f"No strong evidence for {label}: {node.notes}",
                ))

        confidence = round(confidence / weight_total, 2) if weight_total > 0 else 0.0

        if confidence >= 0.70:
            status = PolicyStatus.PASS
        elif confidence >= 0.40:
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
