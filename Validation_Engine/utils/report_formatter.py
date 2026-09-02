"""
Report aggregation & summary formatting helpers.
"""

from typing import List, Tuple
from base_validator import ValidationResult, ValidationStatus

class ReportFormatter:
    """Formats validation summaries, warnings, and errors for ValidationReport."""

    @staticmethod
    def compute_overall_status(results: List[ValidationResult]) -> ValidationStatus:
        """
        Deterministic status rule:
        Any FAIL -> FAIL
        No FAIL and >= 1 WARNING -> WARNING
        All PASS or SKIPPED -> PASS
        """
        has_fail = any(r.status == ValidationStatus.FAIL for r in results)
        if has_fail:
            return ValidationStatus.FAIL
            
        has_warning = any(r.status == ValidationStatus.WARNING for r in results)
        if has_warning:
            return ValidationStatus.WARNING

        return ValidationStatus.PASS

    @staticmethod
    def extract_warnings_and_errors(results: List[ValidationResult]) -> Tuple[List[str], List[str]]:
        """Extracts text warnings and errors from validator results and findings."""
        warnings: List[str] = []
        errors: List[str] = []

        for r in results:
            if r.status == ValidationStatus.FAIL:
                errors.extend(r.messages)
            elif r.status == ValidationStatus.WARNING:
                warnings.extend(r.messages)

            for f in r.findings:
                msg = f"[{f.code}] {f.severity.value}: {f.message}"
                if f.severity.value in ["HIGH", "CRITICAL"]:
                    errors.append(msg)
                elif f.severity.value in ["MEDIUM", "LOW"]:
                    warnings.append(msg)

        return warnings, errors
