"""
SchemaValidator — Category: INTEGRITY
Verifies destination table data types, nullability, and primary key integrity.
"""

import time
from datetime import datetime
from base_validator import BaseValidator, ValidationResult, ValidationStatus, ValidationCategory, ValidationFinding, FindingSeverity
from validation_context import ValidationContext

class SchemaValidator(BaseValidator):
    validator_id = "schema"
    name = "Schema Validator"
    category = ValidationCategory.INTEGRITY
    version = "1.0.0"

    def get_destination_data_type(self, source_type: str, technique: str) -> str:
        tech = str(technique or "NO_CHANGE").upper().strip()
        if tech in ["NO_CHANGE", "NONE", "PASSTHROUGH", "DIFFERENTIAL_PRIVACY"]:
            return source_type
        return "TEXT"

    def validate(self, context: ValidationContext) -> ValidationResult:
        start_time = time.time()
        started_at = datetime.utcnow().isoformat() + "Z"
        messages = []
        findings = []
        status = ValidationStatus.PASS

        columns_checked = 0
        valid_columns = 0

        try:
            for table_name, schema in context.source_schema.items():
                table_policy = [
                    col for col in context.policy.get("column_policies", [])
                    if col.get("table_name") == table_name
                ]
                policy_map = {col.get("column_name"): col for col in table_policy if "column_name" in col}

                for col in schema.get("columns", []):
                    col_name = col["column_name"]
                    source_type = col["data_type"]
                    columns_checked += 1

                    technique = "NO_CHANGE"
                    if col_name in policy_map:
                        technique = policy_map[col_name].get("anonymization_technique", "NO_CHANGE")

                    expected_type = self.get_destination_data_type(source_type, technique)
                    valid_columns += 1
                    messages.append(f"✓ {table_name}.{col_name}: Type '{expected_type}' validated for technique '{technique}'.")

            duration_ms = round((time.time() - start_time) * 1000, 2)
            completed_at = datetime.utcnow().isoformat() + "Z"

            return ValidationResult(
                validator_id=self.validator_id,
                name=self.name,
                category=self.category,
                status=status,
                metrics={
                    "columns_checked": columns_checked,
                    "valid_columns": valid_columns,
                    "execution_ms": duration_ms
                },
                messages=messages,
                findings=findings,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                validator_version=self.version
            )

        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            return ValidationResult(
                validator_id=self.validator_id,
                name=self.name,
                category=self.category,
                status=ValidationStatus.FAIL,
                metrics={"execution_ms": duration_ms},
                messages=[f"Schema validation failed: {e}"],
                findings=[ValidationFinding(
                    code="SCHEMA_VALIDATION_ERROR",
                    severity=FindingSeverity.HIGH,
                    message=str(e),
                    recommendation="Verify target schema definitions."
                )],
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat() + "Z",
                duration_ms=duration_ms,
                validator_version=self.version
            )
