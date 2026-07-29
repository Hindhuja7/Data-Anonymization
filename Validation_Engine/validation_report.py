"""
ValidationReport dataclass — single immutable source of truth for Step 14, UI, Step 15, Step 16, and REST APIs.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from base_validator import ValidationStatus, ValidationResult

@dataclass
class ValidationReport:
    execution_id: str
    overall_status: ValidationStatus
    validation_results: List[ValidationResult]
    privacy_score: int
    risk_score: float
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    completed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    report_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_version": self.report_version,
            "execution_id": self.execution_id,
            "overall_status": self.overall_status.value,
            "validation_results": [r.to_dict() for r in self.validation_results],
            "privacy_score": self.privacy_score,
            "risk_score": self.risk_score,
            "warnings": self.warnings,
            "errors": self.errors,
            "execution_time_ms": self.execution_time_ms,
            "completed_at": self.completed_at
        }
