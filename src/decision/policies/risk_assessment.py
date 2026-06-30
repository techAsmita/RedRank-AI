"""
risk_assessment.py
---------------------
Risk Assessment policy.

Question: What hiring risks exist for this candidate?

Note: unlike other policies, a higher confidence here means
LOWER risk (fewer red flags), not stronger qualification.
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


class RiskAssessmentPolicy(DecisionPolicyInterface):

    @property
    def policy(self) -> DecisionPolicy:
        return DecisionPolicy(
            id="risk_assessment",
            name="Risk Assessment",
            description="Identifies hiring risks: timeline gaps, job hopping, skill inflation, suspicious profiles.",
        )

    def evaluate(self, context: DecisionContext) -> PolicyResult:
        risk = context.candidate_intelligence.risk
        graph = context.evidence_graph

        evidence = []
        concerns = []
        trace = []

        node = graph.risk_flags
        confidence = node.strength

        trace.append(DecisionTrace(
            step="Risk Flag Count",
            observation=f"{risk.risk_flag_count} flags triggered",
            outcome="low risk" if risk.risk_flag_count == 0 else "flags present",
        ))

        if risk.has_timeline_gaps:
            concerns.append(DecisionEvidence(
                source="Candidate Intelligence",
                field="Timeline Gap",
                value=f"{risk.timeline_gap_months} months",
                explanation="Unexplained gap detected between roles.",
            ))
        if risk.has_timeline_overlap:
            concerns.append(DecisionEvidence(
                source="Candidate Intelligence",
                field="Timeline Overlap",
                value=f"{risk.overlap_count} overlaps",
                explanation="Overlapping employment dates detected — may indicate data inconsistency.",
            ))
        if risk.job_hopping_flag:
            concerns.append(DecisionEvidence(
                source="Candidate Intelligence",
                field="Job Hopping",
                value="flagged",
                explanation="More than half of roles lasted under 12 months.",
            ))
        if risk.skill_inflation_flag:
            concerns.append(DecisionEvidence(
                source="Candidate Intelligence",
                field="Skill Inflation",
                value="flagged",
                explanation="Unusually high skill count relative to total experience.",
            ))
        if risk.suspicious_skill_count:
            concerns.append(DecisionEvidence(
                source="Candidate Intelligence",
                field="Suspicious Skill Count",
                value="flagged",
                explanation="Skill count combined with very low experience suggests possible keyword stuffing.",
            ))
        if risk.missing_dates_ratio > 0.5:
            concerns.append(DecisionEvidence(
                source="Candidate Intelligence",
                field="Missing Dates",
                value=f"{risk.missing_dates_ratio:.2f}",
                explanation="Majority of roles have incomplete date information.",
            ))
        if risk.short_descriptions_ratio > 0.5:
            concerns.append(DecisionEvidence(
                source="Candidate Intelligence",
                field="Short Descriptions",
                value=f"{risk.short_descriptions_ratio:.2f}",
                explanation="Majority of role descriptions are very brief, limiting verifiable detail.",
            ))

        if risk.risk_flag_count == 0:
            evidence.append(DecisionEvidence(
                source="Evidence Graph",
                field="Risk Flags",
                value="0",
                explanation="No risk flags triggered across timeline, skills, or job stability checks.",
            ))
        elif not concerns:
            # A flag was counted by the Evidence Graph's aggregate risk score,
            # but none of the explicit checks above matched it directly.
            # Surface the aggregate count itself so the conclusion stays traceable.
            concerns.append(DecisionEvidence(
                source="Evidence Graph",
                field="Risk Flags",
                value=str(risk.risk_flag_count),
                explanation=f"{risk.risk_flag_count} aggregate risk flag(s) detected by the Evidence Graph; see decision trace for the underlying signal.",
            ))

        confidence = round(confidence, 2)

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
