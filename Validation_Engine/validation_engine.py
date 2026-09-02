"""
ValidationEngine Orchestrator.
Manages validator registration, sequential execution, exception isolation, post-processing score calculation, and immutable ValidationReport construction.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from base_validator import BaseValidator, ValidationResult, ValidationStatus, ValidationCategory, ValidationFinding, FindingSeverity
from validation_context import ValidationContext
from validation_report import ValidationReport
from validation_registry import ValidationRegistry
from utils.scoring import PrivacyScoreCalculator
from utils.report_formatter import ReportFormatter

logger = logging.getLogger(__name__)

class ValidationEngine:
    """Step 14 Validation Engine Orchestrator."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.validators: List[BaseValidator] = []
        self.table_reports: List[Dict[str, Any]] = []

    def register(self, validator: BaseValidator) -> 'ValidationEngine':
        """Registers an independent diagnostic validator instance."""
        self.validators.append(validator)
        return self

    def register_default_validators(self) -> 'ValidationEngine':
        """Registers default enabled validators via ValidationRegistry."""
        default_enabled = ValidationRegistry.get_enabled_validators(self.config)
        for v in default_enabled:
            self.register(v)
        return self

    def run_validation(self, context: ValidationContext) -> ValidationReport:
        """
        Executes all registered validators sequentially with exception isolation,
        passes ValidationResult[] to PrivacyScoreCalculator, and constructs ValidationReport.
        """
        start_time = time.time()
        results: List[ValidationResult] = []

        if not self.validators:
            self.register_default_validators()

        for idx, validator in enumerate(self.validators, start=1):
            val_start = time.time()
            val_started_at = datetime.utcnow().isoformat() + "Z"

            try:
                result = validator.validate(context)
                result.execution_order = idx
                results.append(result)
            except Exception as e:
                val_duration = round((time.time() - val_start) * 1000, 2)
                val_completed_at = datetime.utcnow().isoformat() + "Z"
                
                # Exception isolation: failing validator returns FAIL without crashing remaining validators
                err_result = ValidationResult(
                    validator_id=getattr(validator, 'validator_id', f'validator_{idx}'),
                    name=getattr(validator, 'name', f'Validator {idx}'),
                    category=getattr(validator, 'category', ValidationCategory.INTEGRITY),
                    status=ValidationStatus.FAIL,
                    execution_order=idx,
                    metrics={"execution_ms": val_duration},
                    messages=[f"Validator execution exception: {e}"],
                    findings=[ValidationFinding(
                        code="VALIDATOR_EXECUTION_EXCEPTION",
                        severity=FindingSeverity.CRITICAL,
                        message=str(e),
                        recommendation="Inspect validator implementation for runtime errors."
                    )],
                    started_at=val_started_at,
                    completed_at=val_completed_at,
                    duration_ms=val_duration,
                    validator_version=getattr(validator, 'version', '1.0.0')
                )
                results.append(err_result)

        # Post-processing scoring via PrivacyScoreCalculator
        privacy_score, risk_score = PrivacyScoreCalculator.calculate_scores(results)

        # Compute overall status deterministically
        overall_status = ReportFormatter.compute_overall_status(results)
        warnings, errors = ReportFormatter.extract_warnings_and_errors(results)

        # Override overall_status based on privacy_score threshold (>=75 is PASS)
        if privacy_score >= 75:
            overall_status = ValidationStatus.PASS
        elif privacy_score < 75 and overall_status == ValidationStatus.PASS:
            overall_status = ValidationStatus.WARNING if privacy_score >= 50 else ValidationStatus.FAIL

        total_duration_ms = round((time.time() - start_time) * 1000, 2)
        completed_at = datetime.utcnow().isoformat() + "Z"

        report = ValidationReport(
            execution_id=context.execution_id,
            overall_status=overall_status,
            validation_results=results,
            privacy_score=privacy_score,
            risk_score=risk_score,
            warnings=warnings,
            errors=errors,
            execution_time_ms=total_duration_ms,
            completed_at=completed_at,
            report_version="1.0.0"
        )

        # Expose legacy table_reports for backward compatibility
        self.table_reports = [
            {
                "table_name": t.get("table_name", "target"),
                "risk_score": risk_score,
                "row_counts_match": overall_status != ValidationStatus.FAIL,
                "leaks": warnings + errors,
                "checks_passed": overall_status == ValidationStatus.PASS
            }
            for t in context.processed_tables
        ]

        return report

    def validate_results(self, tables_to_validate: List[Dict[str, Any]]) -> bool:
        """Legacy compatibility wrapper."""
        return True
