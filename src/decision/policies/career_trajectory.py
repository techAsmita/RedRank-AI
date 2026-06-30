"""
career_trajectory.py
---------------------
Career Trajectory policy.

Question: Does the candidate demonstrate healthy career growth and stability?
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


class CareerTrajectoryPolicy(DecisionPolicyInterface):

    @property
    def policy(self) -> DecisionPolicy:
        return DecisionPolicy(
            id="career_trajectory",
            name="Career Trajectory",
            description="Evaluates career progression, stability, and growth.",
        )

    def evaluate(self, context: DecisionContext) -> PolicyResult:
        career = context.candidate_intelligence.career
        graph = context.evidence_graph

        evidence = []
        concerns = []
        trace = []
        confidence = 0.0

        # Career growth rate, 40% weight
        node = graph.career_growth
        confidence += node.strength * 0.40
        trace.append(DecisionTrace(
            step="Career Growth",
            observation=f"rate={career.career_growth_rate:.2f}/yr, strength={node.strength:.2f}",
            outcome="satisfied" if node.satisfied else "not satisfied",
        ))
        if node.satisfied:
            evidence.append(DecisionEvidence(
                source="Evidence Graph",
                field="Career Growth",
                value=f"{career.career_growth_rate:.2f}/yr",
                explanation=node.notes,
            ))
        else:
            concerns.append(DecisionEvidence(
                source="Evidence Graph",
                field="Career Growth",
                value=f"{career.career_growth_rate:.2f}/yr",
                explanation=node.notes,
            ))

        # Job stability, 30% weight
        if not career.job_hopping_flag:
            confidence += 0.30
            evidence.append(DecisionEvidence(
                source="Candidate Intelligence",
                field="Job Stability",
                value=f"hop_rate={career.job_hopping_rate:.2f}",
                explanation="No significant job hopping detected.",
            ))
            trace.append(DecisionTrace(
                step="Job Stability",
                observation=f"hop_rate={career.job_hopping_rate:.2f}",
                outcome="stable",
            ))
        else:
            concerns.append(DecisionEvidence(
                source="Candidate Intelligence",
                field="Job Stability",
                value=f"hop_rate={career.job_hopping_rate:.2f}",
                explanation="Frequent short tenures detected (job hopping flag triggered).",
            ))
            trace.append(DecisionTrace(
                step="Job Stability",
                observation=f"hop_rate={career.job_hopping_rate:.2f}",
                outcome="unstable",
            ))

        # Sufficient experience, 30% weight
        node = graph.experience_years
        confidence += node.strength * 0.30
        trace.append(DecisionTrace(
            step="Experience Years",
            observation=f"{career.total_experience_years}y total",
            outcome="satisfied" if node.satisfied else "not satisfied",
        ))
        if node.satisfied:
            evidence.append(DecisionEvidence(
                source="Evidence Graph",
                field="Experience",
                value=f"{career.total_experience_years} years",
                explanation=node.notes,
            ))
        else:
            concerns.append(DecisionEvidence(
                source="Evidence Graph",
                field="Experience",
                value=f"{career.total_experience_years} years",
                explanation=node.notes,
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
