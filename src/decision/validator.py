"""
validator.py
-------------
Evidence Validator.

Independently audits every PolicyResult after policy evaluation.
Enforces one non-negotiable rule:

    Every PASS or FAIL conclusion must reference at least one
    piece of evidence or concern. A confident conclusion with
    zero supporting facts is rejected.

This is a second line of defense. Policies are responsible for
referencing evidence themselves; this module catches anything
that slips through — a missing evidence reference in any policy
is treated as a defect, not an acceptable outcome.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from src.decision.models import PolicyResult, PolicyStatus


@dataclass
class ValidationIssue:
    """A single validation failure found in a PolicyResult."""
    policy_name: str
    issue: str
    severity: str  # "ERROR" | "WARNING"


@dataclass
class ValidationReport:
    """
    Result of validating a full set of PolicyResults.

    is_valid is True only if there are zero ERROR-level issues.
    WARNING-level issues do not block validity but should be reviewed.
    """
    is_valid: bool = True
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "ERROR"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "WARNING"]


class EvidenceValidator:
    """
    Validates that every policy conclusion is evidence-backed.

    Reusable across any list of PolicyResult objects, regardless
    of which policies produced them.
    """

    def validate(self, results: List[PolicyResult]) -> ValidationReport:
        """
        Validate a full set of policy results.

        Rules enforced:
        1. PASS or FAIL status must have at least one evidence
           or concern item — a confident conclusion needs a reason.
        2. PARTIAL status should ideally have both evidence and
           concerns (a partial result implies a tradeoff was found),
           but a single-sided PARTIAL is a WARNING, not an ERROR.
        3. Confidence must be in the valid [0.0, 1.0] range.
        4. supporting_evidence and concerns must not contain
           duplicate (field, value) pairs — a sign of double-counting.
        """
        issues: List[ValidationIssue] = []

        for result in results:
            issues.extend(self._validate_single(result))

        is_valid = not any(i.severity == "ERROR" for i in issues)

        return ValidationReport(is_valid=is_valid, issues=issues)

    def _validate_single(self, result: PolicyResult) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        total_support = len(result.supporting_evidence) + len(result.concerns)

        # Rule 1: confident conclusions need evidence
        if result.status in (PolicyStatus.PASS, PolicyStatus.FAIL):
            if total_support == 0:
                issues.append(ValidationIssue(
                    policy_name=result.policy_name,
                    issue=(
                        f"Status is {result.status.value} but no supporting "
                        f"evidence or concerns were referenced."
                    ),
                    severity="ERROR",
                ))

        # Rule 2: PARTIAL should show both sides where possible
        if result.status == PolicyStatus.PARTIAL:
            if not result.supporting_evidence and not result.concerns:
                issues.append(ValidationIssue(
                    policy_name=result.policy_name,
                    issue="PARTIAL status has no evidence or concerns at all.",
                    severity="ERROR",
                ))
            elif not result.supporting_evidence or not result.concerns:
                issues.append(ValidationIssue(
                    policy_name=result.policy_name,
                    issue=(
                        "PARTIAL status is one-sided (only evidence or only "
                        "concerns); a tradeoff conclusion typically has both."
                    ),
                    severity="WARNING",
                ))

        # Rule 3: confidence range
        if not (0.0 <= result.confidence <= 1.0):
            issues.append(ValidationIssue(
                policy_name=result.policy_name,
                issue=f"Confidence {result.confidence} is outside the valid [0.0, 1.0] range.",
                severity="ERROR",
            ))

        # Rule 4: duplicate evidence detection
        seen = set()
        for e in result.supporting_evidence + result.concerns:
            key = (e.field, e.value)
            if key in seen:
                issues.append(ValidationIssue(
                    policy_name=result.policy_name,
                    issue=f"Duplicate evidence reference for field '{e.field}' with value '{e.value}'.",
                    severity="WARNING",
                ))
            seen.add(key)

        return issues
