"""
professional_signals.py
-------------------------
Professional Signals policy.

Question: Does the profile demonstrate engineering maturity
and professional engagement?

Sources: GitHub presence, certifications, profile completeness.
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


class ProfessionalSignalsPolicy(DecisionPolicyInterface):

    @property
    def policy(self) -> DecisionPolicy:
        return DecisionPolicy(
            id="professional_signals",
            name="Professional Signals",
            description="Evaluates engineering maturity through GitHub presence, certifications, and profile quality.",
        )

    def evaluate(self, context: DecisionContext) -> PolicyResult:
        graph = context.evidence_graph
        behavior = context.candidate_intelligence.behavior

        evidence = []
        concerns = []
        trace = []
        confidence = 0.0

        # GitHub presence, 40% weight
        node = graph.github_presence
        confidence += node.strength * 0.40
        trace.append(DecisionTrace(
            step="GitHub Presence",
            observation=f"strength={node.strength:.2f}",
            outcome="satisfied" if node.satisfied else "not satisfied",
        ))
        if node.satisfied:
            evidence.append(DecisionEvidence(
                source="Evidence Graph",
                field="GitHub",
                value=f"{node.strength:.2f}",
                explanation=node.notes,
            ))
        else:
            concerns.append(DecisionEvidence(
                source="Evidence Graph",
                field="GitHub",
                value=f"{node.strength:.2f}",
                explanation="No public GitHub or portfolio found.",
            ))

        # Certifications, 30% weight
        node = graph.certifications
        confidence += node.strength * 0.30
        trace.append(DecisionTrace(
            step="Certifications",
            observation=f"count={behavior.certification_count}",
            outcome="satisfied" if node.satisfied else "not satisfied",
        ))
        if node.satisfied:
            evidence.append(DecisionEvidence(
                source="Evidence Graph",
                field="Certifications",
                value=f"{behavior.certification_count} certs",
                explanation=node.notes,
            ))

        # Profile quality, 30% weight
        node = graph.profile_quality
        confidence += node.strength * 0.30
        trace.append(DecisionTrace(
            step="Profile Quality",
            observation=f"completeness={behavior.profile_completeness:.2f}",
            outcome="satisfied" if node.satisfied else "not satisfied",
        ))
        if node.satisfied:
            evidence.append(DecisionEvidence(
                source="Evidence Graph",
                field="Profile Quality",
                value=f"{int(behavior.profile_completeness * 100)}%",
                explanation=node.notes,
            ))
        else:
            concerns.append(DecisionEvidence(
                source="Evidence Graph",
                field="Profile Quality",
                value=f"{int(behavior.profile_completeness * 100)}%",
                explanation="Incomplete profile — missing key sections.",
            ))

        confidence = round(min(confidence, 1.0), 2)

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
