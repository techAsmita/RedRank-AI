"""
jd_intent_coverage.py
------------------------
JD Intent Coverage policy.

Question: How well does the candidate satisfy the hiring manager's
intent — across technical, career, and behavioral dimensions of
the JobIntent — not just keyword overlap?
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


class JDIntentCoveragePolicy(DecisionPolicyInterface):

    @property
    def policy(self) -> DecisionPolicy:
        return DecisionPolicy(
            id="jd_intent_coverage",
            name="JD Intent Coverage",
            description="Evaluates how well the candidate satisfies the recruiter's underlying intent.",
        )

    def evaluate(self, context: DecisionContext) -> PolicyResult:
        job = context.job_intent
        graph = context.evidence_graph
        career = context.candidate_intelligence.career
        behavior_intel = context.candidate_intelligence.behavior

        evidence = []
        concerns = []
        trace = []
        confidence = 0.0
        weight_total = 0.0

        # Technical intent dimensions (50% total weight, split across whatever JD requires)
        technical_checks = []
        if job.technical.python_required:
            technical_checks.append(("Python", graph.python))
        if job.technical.retrieval:
            technical_checks.append(("Retrieval", graph.retrieval))
        if job.technical.evaluation:
            technical_checks.append(("Evaluation", graph.evaluation))
        if job.technical.mlops:
            technical_checks.append(("MLOps", graph.mlops))
        if job.technical.cloud_required:
            technical_checks.append(("Cloud", graph.cloud))
        if job.technical.production_ai:
            technical_checks.append(("Production AI", graph.production_ai))

        if technical_checks:
            per_weight = 0.50 / len(technical_checks)
            for label, node in technical_checks:
                weight_total += per_weight
                confidence += node.strength * per_weight
                trace.append(DecisionTrace(
                    step=f"Intent: {label}",
                    observation=f"strength={node.strength:.2f}",
                    outcome="covered" if node.satisfied else "gap",
                ))
                if node.satisfied:
                    evidence.append(DecisionEvidence(
                        source="Evidence Graph",
                        field=label,
                        value=f"{node.strength:.2f}",
                        explanation=f"JD requires {label}; candidate shows {node.notes.lower()}.",
                    ))
                else:
                    concerns.append(DecisionEvidence(
                        source="Evidence Graph",
                        field=label,
                        value=f"{node.strength:.2f}",
                        explanation=f"JD requires {label}; gap in candidate evidence.",
                    ))

        # Career intent: minimum experience years (25% weight)
        if job.career.minimum_experience_years:
            weight_total += 0.25
            required = job.career.minimum_experience_years
            actual = career.total_experience_years
            met = actual >= required
            strength = min(actual / required, 1.0) if required > 0 else 1.0
            confidence += strength * 0.25
            trace.append(DecisionTrace(
                step="Intent: Experience",
                observation=f"{actual}y actual vs {required}y required",
                outcome="covered" if met else "gap",
            ))
            if met:
                evidence.append(DecisionEvidence(
                    source="Candidate Intelligence",
                    field="Experience",
                    value=f"{actual}y",
                    explanation=f"Meets the JD's minimum {required}y requirement.",
                ))
            else:
                concerns.append(DecisionEvidence(
                    source="Candidate Intelligence",
                    field="Experience",
                    value=f"{actual}y",
                    explanation=f"Below the JD's minimum {required}y requirement.",
                ))

        # Behavioral intent: ownership, product mindset, communication (25% weight)
        behavior_checks = []
        if job.behavior.ownership:
            behavior_checks.append("ownership")
        if job.behavior.product_mindset:
            behavior_checks.append("product_mindset")
        if job.behavior.communication:
            behavior_checks.append("communication")

        if behavior_checks:
            weight_total += 0.25
            # We don't have direct behavioral proof signals beyond GitHub/certs,
            # so we treat professional engagement as a reasonable proxy and flag
            # explicitly that this is indirect evidence.
            proxy_strength = graph.github_presence.strength * 0.5 + graph.profile_quality.strength * 0.5
            confidence += proxy_strength * 0.25
            trace.append(DecisionTrace(
                step="Intent: Behavioral signals",
                observation=f"JD values: {', '.join(behavior_checks)}",
                outcome=f"proxy_strength={proxy_strength:.2f} (indirect evidence only)",
            ))
            concerns.append(DecisionEvidence(
                source="Job Intent",
                field="Behavioral Intent",
                value=', '.join(behavior_checks),
                explanation="JD values behavioral traits not directly observable from available data; using GitHub/profile quality as an indirect proxy.",
            ))

        confidence = round(confidence / weight_total, 2) if weight_total > 0 else 0.5

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
