"""
ValidationRegistry factory — instantiates enabled validators based on configuration.
"""

from typing import List, Dict, Any
from base_validator import BaseValidator, ValidationResult, ValidationStatus, ValidationCategory, ValidationFinding, FindingSeverity
from validators import (
    RowCountValidator,
    SchemaValidator,
    RegexLeakScanner,
    ThiefAgent,
    ComplianceValidator
)

DEFAULT_VALIDATION_CONFIG: Dict[str, Dict[str, bool]] = {
    "row_count": {"enabled": True},
    "schema": {"enabled": True},
    "regex_leak": {"enabled": True},
    "thief_agent": {"enabled": True},
    "compliance": {"enabled": True}
}

class ValidationRegistry:
    """Factory loading and instantiating enabled diagnostic validators."""

    @staticmethod
    def get_enabled_validators(config: Dict[str, Any] = None) -> List[BaseValidator]:
        cfg = config.get("validation", DEFAULT_VALIDATION_CONFIG) if config else DEFAULT_VALIDATION_CONFIG
        
        all_validators = [
            RowCountValidator(),
            SchemaValidator(),
            RegexLeakScanner(),
            ThiefAgent(),
            ComplianceValidator()
        ]

        enabled = []
        for v in all_validators:
            v_cfg = cfg.get(v.validator_id, {"enabled": True})
            if v_cfg.get("enabled", True):
                enabled.append(v)

        return enabled
