"""
production_readiness.py
------------------------
Production Readiness policy.

Question: Has the candidate built and operated production systems?
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


class ProductionReadinessPolicy(DecisionPolicyInterface):

    @property
    def policy(self) -> DecisionPolicy:
        return DecisionPolicy(
            id="production_readiness",
            name="Production Readiness",
            description="Evaluates whether the candidate has deployed and operated production systems.",
        )

    def evaluate(self, context: DecisionContext) -> PolicyResult:
        graph = context.evidence_graph

        evidence = []
        concerns = []
        trace = []
        confidence = 0.0

        # Production AI evidence (primary signal, 50% weight)
        node = graph.production_ai
        confidence += node.strength * 0.50
        trace.append(DecisionTrace(
            step="Production AI",
            observation=f"strength={node.strength:.2f}",
            outcome="satisfied" if node.satisfied else "not satisfied",
        ))
        if node.satisfied:
            evidence.append(DecisionEvidence(
                source="Evidence Graph",
                field="Production AI",
                value=f"{node.strength:.2f}",
                explanation=node.notes,
            ))
        else:
            concerns.append(DecisionEvidence(
                source="Evidence Graph",
                field="Production AI",
                value=f"{node.strength:.2f}",
                explanation="No evidence of deployed production AI systems.",
            ))

        # MLOps tooling evidence (operational maturity, 25% weight)
        node = graph.mlops
        confidence += node.strength * 0.25
        trace.append(DecisionTrace(
            step="MLOps",
            observation=f"strength={node.strength:.2f}",
            outcome="satisfied" if node.satisfied else "not satisfied",
        ))
        if node.satisfied:
            evidence.append(DecisionEvidence(
                source="Evidence Graph",
                field="MLOps",
                value=f"{node.strength:.2f}",
                explanation=node.notes,
            ))

        # AI experience duration (sustained production exposure, 25% weight)
        node = graph.ai_experience
        confidence += node.strength * 0.25
        trace.append(DecisionTrace(
            step="AI Experience",
            observation=f"strength={node.strength:.2f}",
            outcome="satisfied" if node.satisfied else "not satisfied",
        ))
        if node.satisfied:
            evidence.append(DecisionEvidence(
                source="Evidence Graph",
                field="AI Experience",
                value=f"{node.strength:.2f}",
                explanation=node.notes,
            ))
        else:
            concerns.append(DecisionEvidence(
                source="Evidence Graph",
                field="AI Experience",
                value=f"{node.strength:.2f}",
                explanation="Limited sustained AI/ML experience.",
            ))

        confidence = round(min(confidence, 1.0), 2)

        if confidence >= 0.70:
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
