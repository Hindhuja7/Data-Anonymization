"""
Base models, enums, dataclasses, and abstract interface for Step 14 Pluggable Validators.
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

class ValidationStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"

class ValidationCategory(str, Enum):
    INTEGRITY = "INTEGRITY"
    SECURITY = "SECURITY"
    COMPLIANCE = "COMPLIANCE"

class FindingSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class ValidationFinding:
    code: str
    severity: FindingSeverity
    message: str
    recommendation: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "recommendation": self.recommendation,
            "details": self.details
        }

@dataclass
class ValidationResult:
    validator_id: str
    name: str
    category: ValidationCategory
    status: ValidationStatus
    execution_order: int = 1
    metrics: Dict[str, Any] = field(default_factory=dict)
    messages: List[str] = field(default_factory=list)
    findings: List[ValidationFinding] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    completed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    duration_ms: float = 0.0
    validator_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validator_id": self.validator_id,
            "name": self.name,
            "category": self.category.value,
            "status": self.status.value,
            "execution_order": self.execution_order,
            "metrics": self.metrics,
            "messages": self.messages,
            "findings": [f.to_dict() for f in self.findings],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "validator_version": self.validator_version
        }

class BaseValidator(ABC):
    """Abstract base class for all Step 14 diagnostic validators."""
    
    validator_id: str = "base_validator"
    name: str = "Base Validator"
    category: ValidationCategory = ValidationCategory.INTEGRITY
    version: str = "1.0.0"

    @abstractmethod
    def validate(self, context) -> ValidationResult:
        """
        Executes diagnostic validation against the lightweight ValidationContext.
        Must return a populated ValidationResult object.
        """
        pass
