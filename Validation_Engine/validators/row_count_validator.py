"""
RowCountValidator — Category: INTEGRITY
Compares source vs destination record counts.
"""

import time
from datetime import datetime
from base_validator import BaseValidator, ValidationResult, ValidationStatus, ValidationCategory, ValidationFinding, FindingSeverity
from validation_context import ValidationContext
from sqlalchemy import text

class RowCountValidator(BaseValidator):
    validator_id = "row_count"
    name = "Row Count Validator"
    category = ValidationCategory.INTEGRITY
    version = "1.0.0"

    def validate(self, context: ValidationContext) -> ValidationResult:
        start_time = time.time()
        started_at = datetime.utcnow().isoformat() + "Z"
        messages = []
        findings = []
        status = ValidationStatus.PASS

        rows_checked = 0
        rows_matched = 0
        table_counts = {}

        try:
            for t in context.processed_tables:
                table_name = t.get("table_name")
                if not table_name:
                    continue

                # Query source count
                src_count = 0
                with context.source_connector.engine.connect() as conn:
                    dialect = context.source_connector.engine.name.lower()
                    sql_str = f'SELECT COUNT(*) FROM `{table_name}`' if 'mysql' in dialect else f'SELECT COUNT(*) FROM "{table_name}"'
                    res = conn.execute(text(sql_str))
                    src_count = res.scalar() or 0

                # Query destination count
                dest_count = 0
                with context.destination_connector.engine.connect() as conn:
                    dialect = context.destination_connector.engine.name.lower()
                    sql_str = f'SELECT COUNT(*) FROM `{table_name}`' if 'mysql' in dialect else f'SELECT COUNT(*) FROM "{table_name}"'
                    res = conn.execute(text(sql_str))
                    dest_count = res.scalar() or 0

                rows_checked += src_count
                table_counts[table_name] = {"source": src_count, "destination": dest_count}

                if src_count == dest_count:
                    rows_matched += src_count
                    messages.append(f"✓ Table '{table_name}': Record count matches 100% ({src_count:,} / {dest_count:,}).")
                else:
                    status = ValidationStatus.FAIL
                    msg = f"Mismatch in table '{table_name}': Source has {src_count:,} rows, Destination has {dest_count:,} rows."
                    messages.append(f"✗ {msg}")
                    findings.append(ValidationFinding(
                        code="ROW_COUNT_MISMATCH",
                        severity=FindingSeverity.CRITICAL,
                        message=msg,
                        recommendation=f"Re-run Step 13 destination loading for table '{table_name}'.",
                        details={"table": table_name, "source_count": src_count, "destination_count": dest_count}
                    ))

            duration_ms = round((time.time() - start_time) * 1000, 2)
            completed_at = datetime.utcnow().isoformat() + "Z"

            return ValidationResult(
                validator_id=self.validator_id,
                name=self.name,
                category=self.category,
                status=status,
                metrics={
                    "rows_checked": rows_checked,
                    "rows_matched": rows_matched,
                    "table_counts": table_counts,
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
                messages=[f"Row count validation failed: {e}"],
                findings=[ValidationFinding(
                    code="ROW_COUNT_ERROR",
                    severity=FindingSeverity.CRITICAL,
                    message=str(e),
                    recommendation="Inspect database connections and permissions."
                )],
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat() + "Z",
                duration_ms=duration_ms,
                validator_version=self.version
            )
