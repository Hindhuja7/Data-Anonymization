"""
RegexLeakScanner — Category: SECURITY
High-speed regex scanner scanning destination tables for un-anonymized PII leakage.
"""

import time
import re
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from base_validator import BaseValidator, ValidationResult, ValidationStatus, ValidationCategory, ValidationFinding, FindingSeverity
from validation_context import ValidationContext
from utils.regex_patterns import PII_REGEX_PATTERNS

class RegexLeakScanner(BaseValidator):
    validator_id = "regex_leak"
    name = "Regex Leak Scanner"
    category = ValidationCategory.SECURITY
    version = "1.2.0"

    def validate(self, context: ValidationContext) -> ValidationResult:
        start_time = time.time()
        started_at = datetime.utcnow().isoformat() + "Z"
        messages = []
        findings = []
        status = ValidationStatus.PASS

        total_samples_scanned = 0
        leak_count = 0

        try:
            for t in context.processed_tables:
                table_name = t.get("table_name")
                if not table_name:
                    continue

                dialect = context.destination_connector.engine.name.lower()
                query = f'SELECT * FROM `{table_name}` LIMIT 500' if 'mysql' in dialect else f'SELECT * FROM "{table_name}" LIMIT 500'
                df = pd.read_sql(query, context.destination_connector.engine)
                total_samples_scanned += len(df)

                table_policy = [
                    col for col in context.policy.get("column_policies", [])
                    if col.get("table_name") == table_name
                ]
                policy_map = {col.get("column_name"): col for col in table_policy if "column_name" in col}

                for col_name in df.columns:
                    policy_info = policy_map.get(col_name, {})
                    technique = (policy_info.get("anonymization_technique") or "NO_CHANGE").upper()
                    is_pii = bool(policy_info.get("is_pii", False))
                    pii_type = (policy_info.get("pii_type") or "NON_PII").upper()

                    val_series = df[col_name].dropna().astype(str)
                    
                    # 1. Un-anonymized NO_CHANGE PII column exposure check
                    # Only flag if the column is explicitly designated as PII (is_pii=True) and pii_type is a PII category
                    if is_pii and technique == "NO_CHANGE" and pii_type not in ["NON_PII", "NONE", "NULL"]:
                        status = ValidationStatus.FAIL
                        leak_count += len(val_series)
                        msg = f"CRITICAL LEAK: Raw PII column '{table_name}.{col_name}' ({pii_type}) left un-anonymized (NO_CHANGE) across {len(val_series)} destination records."
                        messages.append(f"❌ {msg}")
                        findings.append(ValidationFinding(
                            code=f"RAW_PII_UNANONYMIZED_EXPOSURE",
                            severity=FindingSeverity.CRITICAL,
                            message=msg,
                            recommendation=f"Update policy for '{table_name}.{col_name}' from NO_CHANGE to MASKING, HASHING, or TOKENIZATION.",
                            details={"table": table_name, "column": col_name, "pii_type": pii_type, "records_exposed": len(val_series), "technique": "NO_CHANGE"}
                        ))

                    # 2. Pattern regex scanning for raw un-anonymized leaks
                    # Note: TOKENIZATION and MASKING intentionally generate realistic synthetic tokens (e.g. fake emails/phones)
                    if technique in ["TOKENIZATION", "MASKING"]:
                        continue

                    for pattern_name, pattern_regex in PII_REGEX_PATTERNS.items():
                        matches = val_series.apply(lambda v: bool(re.search(pattern_regex, v)))
                        match_count = int(matches.sum())
                        if match_count > 0:
                            leak_count += match_count
                            severity = FindingSeverity.CRITICAL if technique == "NO_CHANGE" else (FindingSeverity.HIGH if technique == "HASHING" else FindingSeverity.MEDIUM)
                            if technique == "NO_CHANGE":
                                status = ValidationStatus.FAIL
                            elif status != ValidationStatus.FAIL:
                                status = ValidationStatus.WARNING
                            
                            msg = f"Detected {match_count} raw {pattern_name} pattern matches in '{table_name}.{col_name}' (Technique: {technique})."
                            messages.append(f"⚠ {msg}")
                            findings.append(ValidationFinding(
                                code=f"REGEX_{pattern_name}_LEAK",
                                severity=severity,
                                message=msg,
                                recommendation=f"Review protection technique '{technique}' for column '{col_name}'.",
                                details={"table": table_name, "column": col_name, "pattern": pattern_name, "matches": match_count, "technique": technique}
                            ))

            if leak_count == 0:
                messages.append("✓ Zero raw PII regex leaks detected across sampled destination records.")

            duration_ms = round((time.time() - start_time) * 1000, 2)
            completed_at = datetime.utcnow().isoformat() + "Z"

            return ValidationResult(
                validator_id=self.validator_id,
                name=self.name,
                category=self.category,
                status=status,
                metrics={
                    "total_samples_scanned": total_samples_scanned,
                    "leak_count": leak_count,
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
                messages=[f"Regex leak scanning failed: {e}"],
                findings=[ValidationFinding(
                    code="REGEX_SCANNER_ERROR",
                    severity=FindingSeverity.HIGH,
                    message=str(e),
                    recommendation="Inspect table query execution."
                )],
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat() + "Z",
                duration_ms=duration_ms,
                validator_version=self.version
            )
