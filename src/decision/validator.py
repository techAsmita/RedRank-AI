"""
validator.py
------------
Validation utilities for Decision Policy results.

Purpose
-------
Ensure every policy produces explainable,
evidence-backed decisions.

Validator never changes a decision.

It only reports whether the decision
is structurally valid.
"""

from __future__ import annotations

from src.decision.models import PolicyResult


class DecisionValidator:
    """
    Validates PolicyResult objects.
    """

    @staticmethod
    def validate(result: PolicyResult) -> list[str]:
        """
        Validate a single policy result.

        Returns
        -------
        list[str]

        Empty list means valid.
        """

        errors = []

        if not 0.0 <= result.confidence <= 1.0:
            errors.append(
                "Confidence must be between 0.0 and 1.0."
            )

        if result.status.name == "PASS":

            if not result.supporting_evidence:
                errors.append(
                    "PASS decisions require supporting evidence."
                )

        if result.concerns:

            if not result.decision_trace:
                errors.append(
                    "Concerns require decision trace."
                )

        return errors
