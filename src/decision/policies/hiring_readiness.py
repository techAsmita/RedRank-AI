"""
hiring_readiness.py
---------------------
Hiring Readiness policy.

Question: Can this candidate realistically be hired right now?
Checks notice period, open-to-work status, activity, response rate —
all sourced from the Evidence Graph's availability and profile_quality nodes.
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


class HiringReadinessPolicy(DecisionPolicyInterface):

    @property
    def policy(self) -> DecisionPolicy:
        return DecisionPolicy(
            id="hiring_readiness",
            name="Hiring Readiness",
            description="Evaluates whether the candidate can realistically be hired now.",
        )

    def evaluate(self, context: DecisionContext) -> PolicyResult:
        behavior = context.candidate_intelligence.behavior
        graph = context.evidence_graph

        evidence = []
        concerns = []
        trace = []
        confidence = 0.0

        # Availability evidence (notice period + open to work), 60% weight
        node = graph.availability
        confidence += node.strength * 0.60
        trace.append(DecisionTrace(
            step="Availability",
            observation=f"notice={behavior.notice_period_days}d, open_to_work={behavior.is_open_to_work}",
            outcome="satisfied" if node.satisfied else "not satisfied",
        ))
        if behavior.is_open_to_work:
            evidence.append(DecisionEvidence(
                source="Candidate Intelligence",
                field="Open to Work",
                value="True",
                explanation="Candidate has marked themselves as open to opportunities.",
            ))
        else:
            concerns.append(DecisionEvidence(
                source="Candidate Intelligence",
                field="Open to Work",
                value="False",
                explanation="Candidate has not indicated active job search.",
            ))

        if behavior.notice_period_days is not None:
            if behavior.notice_period_days <= 30:
                evidence.append(DecisionEvidence(
                    source="Candidate Intelligence",
                    field="Notice Period",
                    value=f"{behavior.notice_period_days} days",
                    explanation="Short notice period enables fast hiring turnaround.",
                ))
            elif behavior.notice_period_days > 60:
                concerns.append(DecisionEvidence(
                    source="Candidate Intelligence",
                    field="Notice Period",
                    value=f"{behavior.notice_period_days} days",
                    explanation="Long notice period may delay onboarding.",
                ))

        # Recency of activity, 20% weight
        if behavior.last_active_days is not None:
            recency_strength = max(0.0, 1.0 - (behavior.last_active_days / 30))
            confidence += recency_strength * 0.20
            trace.append(DecisionTrace(
                step="Last Active",
                observation=f"{behavior.last_active_days} days ago",
                outcome="recent" if recency_strength > 0.5 else "stale",
            ))
            if recency_strength > 0.5:
                evidence.append(DecisionEvidence(
                    source="Candidate Intelligence",
                    field="Last Active",
                    value=f"{behavior.last_active_days} days ago",
                    explanation="Candidate has been recently active on the platform.",
                ))
            else:
                concerns.append(DecisionEvidence(
                    source="Candidate Intelligence",
                    field="Last Active",
                    value=f"{behavior.last_active_days} days ago",
                    explanation="Candidate has not been recently active.",
                ))
        else:
            confidence += 0.10  # neutral default if unknown

        # Response rate, 20% weight
        if behavior.response_rate is not None:
            confidence += behavior.response_rate * 0.20
            trace.append(DecisionTrace(
                step="Response Rate",
                observation=f"{behavior.response_rate:.2f}",
                outcome="responsive" if behavior.response_rate >= 0.5 else "low engagement",
            ))
            if behavior.response_rate >= 0.5:
                evidence.append(DecisionEvidence(
                    source="Candidate Intelligence",
                    field="Response Rate",
                    value=f"{behavior.response_rate:.2f}",
                    explanation="Candidate is responsive to recruiter outreach.",
                ))
            else:
                concerns.append(DecisionEvidence(
                    source="Candidate Intelligence",
                    field="Response Rate",
                    value=f"{behavior.response_rate:.2f}",
                    explanation="Low historical response rate to outreach.",
                ))
        else:
            confidence += 0.10  # neutral default if unknown

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
