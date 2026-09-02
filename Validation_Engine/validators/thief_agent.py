"""
ThiefAgent — Category: SECURITY
AI Red-Teaming Auditor evaluating re-identification and linkage attack risk.
"""

import time
import os
import pandas as pd
from datetime import datetime
from base_validator import BaseValidator, ValidationResult, ValidationStatus, ValidationCategory, ValidationFinding, FindingSeverity
from validation_context import ValidationContext

class ThiefAgent(BaseValidator):
    validator_id = "thief_agent"
    name = "The Thief Agent (AI Red-Teaming Auditor)"
    category = ValidationCategory.SECURITY
    version = "2.0.0"

    def validate(self, context: ValidationContext) -> ValidationResult:
        start_time = time.time()
        started_at = datetime.utcnow().isoformat() + "Z"
        messages = []
        findings = []
        status = ValidationStatus.PASS

        reidentification_attempts = 0
        successful_exploits = 0

        try:
            for t in context.processed_tables:
                table_name = t.get("table_name")
                if not table_name:
                    continue

                dialect = context.destination_connector.engine.name.lower()
                query = f'SELECT * FROM `{table_name}` LIMIT 200' if 'mysql' in dialect else f'SELECT * FROM "{table_name}" LIMIT 200'
                df = pd.read_sql(query, context.destination_connector.engine)
                reidentification_attempts += 1

                # 1. Unprotected raw PII red-teaming checks
                table_policy = [
                    col for col in context.policy.get("column_policies", [])
                    if col.get("table_name") == table_name
                ]
                for col in table_policy:
                    col_name = col.get("column_name", "")
                    technique = (col.get("anonymization_technique") or "NO_CHANGE").upper()
                    is_pii = col.get("is_pii", False) or col.get("pii_type", "NONE") != "NONE"
                    if technique == "NO_CHANGE" and is_pii:
                        successful_exploits += 1
                        status = ValidationStatus.FAIL
                        msg = f"Red-Teaming Exploit: Unprotected raw PII column '{table_name}.{col_name}' (NO_CHANGE) exposed to adversary."
                        messages.append(f"❌ {msg}")
                        findings.append(ValidationFinding(
                            code="UNPROTECTED_PII_EXPLOIT",
                            severity=FindingSeverity.CRITICAL,
                            message=msg,
                            recommendation=f"Apply Masking, Hashing, or Tokenization to '{table_name}.{col_name}'.",
                            details={"table": table_name, "column": col_name, "technique": "NO_CHANGE"}
                        ))

                # 2. Rule-based red-teaming checks for quasi-identifier linkages
                columns = [c.lower() for c in df.columns]
                has_dob = any('dob' in c or 'birth' in c or 'date' in c for c in columns)
                has_zip = any('zip' in c or 'pin' in c or 'postal' in c for c in columns)
                has_gender = any('gender' in c or 'sex' in c for c in columns)

                if has_dob and has_zip and has_gender:
                    successful_exploits += 1
                    if status != ValidationStatus.FAIL:
                        status = ValidationStatus.WARNING
                    msg = f"Quasi-identifier linkage vulnerability detected in table '{table_name}': DOB + Zipcode + Gender combined."
                    messages.append(f"⚠ {msg}")
                    findings.append(ValidationFinding(
                        code="QUASI_IDENTIFIER_LINKAGE_RISK",
                        severity=FindingSeverity.MEDIUM,
                        message=msg,
                        recommendation="Apply generalization or differential privacy to quasi-identifiers.",
                        details={"table": table_name, "quasi_identifiers": ["dob", "zipcode", "gender"]}
                    ))

            if successful_exploits == 0:
                messages.append("✓ Zero data leaks or quasi-identifier linkage exploits detected by The Thief Agent.")

            duration_ms = round((time.time() - start_time) * 1000, 2)
            completed_at = datetime.utcnow().isoformat() + "Z"

            return ValidationResult(
                validator_id=self.validator_id,
                name=self.name,
                category=self.category,
                status=status,
                metrics={
                    "reidentification_attempts": reidentification_attempts,
                    "successful_exploits": successful_exploits,
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
                messages=[f"Thief Agent audit failed: {e}"],
                findings=[ValidationFinding(
                    code="THIEF_AGENT_ERROR",
                    severity=FindingSeverity.MEDIUM,
                    message=str(e),
                    recommendation="Verify destination table access."
                )],
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat() + "Z",
                duration_ms=duration_ms,
                validator_version=self.version
            )
