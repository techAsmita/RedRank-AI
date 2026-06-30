"""
evaluator.py
------------
Decision Policy Engine evaluator.

Design decisions:
- Executes policies independently.
- Policies never communicate.
- Returns structured policy results.
- No ranking performed here.
"""

from __future__ import annotations

from src.decision.context import DecisionContext
from src.decision.interfaces import DecisionPolicyInterface
from src.decision.models import DecisionSummary


class DecisionEvaluator:
    """
    Executes every registered decision policy.
    """

    def __init__(
        self,
        policies: list[DecisionPolicyInterface],
    ) -> None:
        self._policies = policies

    def evaluate(
        self,
        context: DecisionContext,
    ) -> DecisionSummary:
        """
        Execute every enabled policy.

        Returns
        -------
        DecisionSummary
        """

        summary = DecisionSummary(
            candidate_id=getattr(
                context.candidate_intelligence,
                "candidate_id",
                "UNKNOWN",
            )
        )

        for policy in self._policies:

            if not policy.policy.enabled:
                continue

            result = policy.evaluate(context)

            summary.policy_results.append(result)

        summary.overall_observations.append(
            f"{len(summary.policy_results)} policies executed."
        )

        return summary
