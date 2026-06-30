"""
interfaces.py
-------------
Shared interfaces for the Decision Policy Engine.

Design decisions:
- Every decision policy follows the same contract.
- Policies are interchangeable.
- Encourages loose coupling and easy testing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.decision.context import DecisionContext
from src.decision.models import (
    DecisionPolicy,
    PolicyResult,
)


class DecisionPolicyInterface(ABC):
    """
    Base interface for every decision policy.

    Every policy must expose:
    - metadata describing the policy
    - one evaluate() method

    Policies must:
    - never modify the DecisionContext
    - never call other policies
    - return exactly one PolicyResult
    """

    @property
    @abstractmethod
    def policy(self) -> DecisionPolicy:
        """
        Metadata describing this policy.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate(
        self,
        context: DecisionContext,
    ) -> PolicyResult:
        """
        Evaluate one hiring dimension.

        Parameters
        ----------
        context:
            Shared DecisionContext.

        Returns
        -------
        PolicyResult
        """
        raise NotImplementedError
