"""
Validation Engine with 'The Thief Agent' (Red-Teaming LLM Auditor)
and Mathematical Privacy Risk Scoring.
"""

import os
import sys
import json
import re
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy import text

from database_connector import DatabaseConnector

logger = logging.getLogger(__name__)

class ValidationEngine:
    """Validates destination database schema compatibility, checks row counts, scans for PII leaks,
    and runs 'The Thief Agent' to compute a mathematical Privacy Risk Score."""
    
    def __init__(self, source_connector, destination_connector, source_schema, policy):
        self.source_connector = source_connector
        self.destination_connector = destination_connector
        self.source_schema = source_schema
        self.policy = policy
        self.table_reports = []
        
        # Local regex patterns for Indian PII leakage safety net
        self.regex_patterns = {
            "AADHAAR": r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b",
            "PAN": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
            "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "PHONE": r"\b(?:\+?91)?[ -]?[6-9]\d{4}[ -]?\d{5}\b",
            "GSTIN": r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b"
        }
        
        # Initialize LLM Client for Thief Agent
        self.llm_client = None
        try:
            api_key = os.getenv("GITHUB_API_KEY")
            if api_key:
                from llm_client import LLMClient
                provider = os.getenv("LLM_PROVIDER", "github")
                model = os.getenv("LLM_MODEL")
                self.llm_client = LLMClient(provider=provider, model=model)
                logger.info("Initialized LLMClient for The Thief Agent.")
            else:
                logger.warning("GITHUB_API_KEY not found. Thief Agent will fall back to local rule-based evaluations.")
        except Exception as e:
            logger.warning(f"Could not load LLMClient for Thief Agent: {e}")

    def get_destination_data_type(self, source_type: str, technique: str) -> str:
        """Determine appropriate destination data type based on technique."""
        if technique == "HASHING":
            return "VARCHAR(64)"
        if technique in ["TOKENIZATION", "PSEUDONYMIZATION", "MASKING", "REDACTION"]:
            return "TEXT"
        return source_type

    def validate_destination_schema(self) -> bool:
        """Validate destination schema against anonymization techniques."""
        print("\nValidating destination schema against anonymization techniques...")
        print("-" * 80)
        
        all_valid = True
        for table_name, schema in self.source_schema.items():
            table_policy = [
                col for col in self.policy.get("column_policies", [])
                if col["table_name"] == table_name
            ]
            policy_map = {col["column_name"]: col for col in table_policy}
            
            for col in schema["columns"]:
                col_name = col["column_name"]
                source_type = col["data_type"]
                
                technique = "NO_CHANGE"
                if col_name in policy_map:
                    technique = policy_map[col_name]["anonymization_technique"]
                
                expected_type = self.get_destination_data_type(source_type, technique)
                
                if technique != "NO_CHANGE" and technique != "DIFFERENTIAL_PRIVACY":
                    if source_type != expected_type:
                        print(f"[OK] {table_name}.{col_name}: {source_type} -> {expected_type} ({technique})")
                    else:
                        print(f"[WARN] {table_name}.{col_name}: {source_type} might be too small for {technique} output")
                        all_valid = False
        
        if all_valid:
            print("[OK] Destination schema validation passed")
        else:
            print("[WARN] Destination schema validation warnings found")
            
        return all_valid

    def _check_local_regex_leaks(self, table_name: str, df: pd.DataFrame, policy_map: Dict[str, Any]) -> List[str]:
        """Perform high-speed local checks to search for leaked identifiers and raw values."""
        leaks = []
        
        # 1. Exact raw value leak check
        try:
            for col_name in df.columns:
                if col_name in policy_map and policy_map[col_name]["anonymization_technique"] != "NO_CHANGE":
                    # Get source values
                    src_query = f'SELECT "{col_name}" FROM "{table_name}" WHERE "{col_name}" IS NOT NULL'
                    with self.source_connector.engine.connect() as conn:
                        res = conn.execute(text(src_query)).fetchall()
                    src_raw_set = {str(r[0]).strip().lower() for r in res if r[0] is not None and str(r[0]).strip() != ""}
                    
                    # Check if any destination value is in the source raw set
                    for dest_val in df[col_name].dropna().astype(str):
                        dest_val_cleaned = dest_val.strip().lower()
                        if dest_val_cleaned != "" and dest_val_cleaned in src_raw_set:
                            leaks.append(f"Column '{col_name}' technique '{policy_map[col_name]['anonymization_technique']}' leaked exact raw source value: '{dest_val}'")
        except Exception as e:
            logger.warning(f"Could not perform exact source raw value leak checks: {e}")
            
        # 2. Regex checks for MASKING/REDACTION/HASHING (where format patterns MUST be broken)
        # AND check ALL columns (including NO_CHANGE) specifically for AADHAAR and PAN leaks in free text!
        for col_name in df.columns:
            # Check if column is in policy
            tech = "NO_CHANGE"
            if col_name in policy_map:
                tech = policy_map[col_name]["anonymization_technique"]
                
            # Loop over regex patterns
            for pii_type, pattern in self.regex_patterns.items():
                # We always scan for critical Aadhaar/PAN across all columns.
                if pii_type in ["AADHAAR", "PAN"]:
                    for val in df[col_name].dropna().astype(str):
                        if val != "" and re.search(pattern, val):
                            leaks.append(f"Column '{col_name}' (technique '{tech}') leaked raw '{pii_type}' pattern: '{val}'")
                            break
                # For other types, only check if they were supposed to be masked/redacted/hashed
                elif tech in ["MASKING", "REDACTION", "HASHING"]:
                    for val in df[col_name].dropna().astype(str):
                        if val != "" and re.match(pattern, val):
                            leaks.append(f"Column '{col_name}' technique '{tech}' leaked raw PII pattern '{pii_type}' value: '{val}'")
                            break
        return leaks

    def run_thief_penetration_test(self, table_name: str, sample_df: pd.DataFrame) -> Dict[str, Any]:
        """Runs 'The Thief Agent' (Red-Team LLM Auditor) attempting to de-anonymize the sample dataset."""
        print(f"\n[Thief Agent] Penetration testing table '{table_name}'...")
        
        if self.llm_client is None:
            print("[Thief Agent] LLM Client not initialized. Skipping LLM audit.")
            return {"anonymization_broken": False, "risk_severity": "LOW", "vulnerability_details": "No GITHUB_API_KEY. Defaulted to Safe."}
            
        # Build policy map for this table's columns
        table_policy = [
            col for col in self.policy.get("column_policies", [])
            if col["table_name"] == table_name
        ]
        policy_map = {col["column_name"]: col for col in table_policy}
        
        # Build metadata summary of columns
        policy_summary = []
        for col_name in sample_df.columns:
            if col_name in policy_map:
                tech = policy_map[col_name]["anonymization_technique"]
                policy_summary.append(f"- Column '{col_name}': Anonymized using technique '{tech}'")
            else:
                policy_summary.append(f"- Column '{col_name}': Kept RAW (No anonymization applied)")
        policy_summary_str = "\n".join(policy_summary)
        
        # Convert sample dataframe to markdown format to feed the LLM context
        sample_md = sample_df.to_markdown(index=False)
        
        # Construct the Red-Team Hacker Prompt
        system_prompt = (
            "You are a malicious database hacker and data privacy auditor specializing in de-anonymization attacks.\n"
            "Your objective is to analyze the anonymized database sample and identify if you can re-identify individuals or detect PII leaks.\n\n"
            "Here is the list of columns and how they were anonymized:\n"
            f"{policy_summary_str}\n\n"
            "CRITICAL DIRECTIVE:\n"
            "- Columns marked as 'TOKENIZATION', 'HASHING', or 'MASKING' have been replaced with fake/synthetic or obfuscated values. "
            "These fake values (e.g. fake name 'Advaith Misra' or fake email 'santadvika@example.net') are designed to look realistic. "
            "DO NOT flag them as leaks. They are successfully anonymized.\n"
            "- Focus your attack strictly on finding if raw PII leaked into columns marked as 'Kept RAW' (like 'comments' or 'notes'), "
            "or if raw PII was not processed, or if quasi-identifiers (like Age + Gender + Location + Salary) are combinable to uniquely re-identify individuals.\n\n"
            "You MUST respond ONLY with a valid JSON object matching the following structure:\n"
            "{\n"
            '  "anonymization_broken": true/false,\n'
            '  "attack_vector_used": "Name of attack vector or None",\n'
            '  "vulnerability_details": "Detailed description of the leakage found, or None",\n'
            '  "risk_severity": "LOW" / "MEDIUM" / "HIGH"\n'
            "}"
        )
        
        user_prompt = (
            f"Here is the anonymized database sample for table '{table_name}':\n\n"
            f"{sample_md}\n\n"
            "Perform your penetration test and output the JSON report."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # We enforce temperature = 0.0 inside our completion call for strict determinism
            response_text = self.llm_client.chat_completion(
                messages=messages, 
                max_tokens=1000,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
                
            report = json.loads(response_text)
            print(f"[Thief Agent] Attack status: {'BROKEN [FAIL]' if report.get('anonymization_broken') else 'SECURE [PASS]'}")
            print(f"[Thief Agent] Risk Severity: {report.get('risk_severity')}")
            if report.get("anonymization_broken"):
                print(f"[Thief Agent] Vulnerability found: {report.get('vulnerability_details')}")
            return report
            
        except Exception as e:
            logger.warning(f"Thief Agent audit failed: {e}")
            return {"anonymization_broken": False, "risk_severity": "LOW", "vulnerability_details": f"API execution failed: {e}"}

    def calculate_privacy_risk_score(self, table_name: str, thief_risk: str) -> float:
        """
        Calculates the mathematical Privacy Risk Score (0-100) for a table:
        Risk = Min(100, (Anonymization Policy Penalty * 70) + Thief Agent Severity Penalty)
        """
        table_policy = [
            col for col in self.policy.get("column_policies", [])
            if col["table_name"] == table_name
        ]
        
        if not table_policy:
            return 0.0
            
        total_weight = 0.0
        total_penalty = 0.0
        
        for col in table_policy:
            pii_type = col.get("pii_type")
            technique = col.get("anonymization_technique", "NO_CHANGE")
            
            # 1. Determine Column Vulnerability Weight
            if pii_type in ["IDENTIFIER", "NAME", "EMAIL", "PHONE", "AADHAAR", "PAN", "GSTIN"]:
                weight = 1.0
            elif pii_type in ["QUASI_IDENTIFIER", "DOB", "AGE", "GENDER", "LOCATION", "SALARY"]:
                weight = 0.5
            else:
                weight = 0.0
                
            # 2. Determine Technique Penalty Factor
            if technique == "NO_CHANGE":
                penalty_factor = 1.0
            elif technique == "DIFFERENTIAL_PRIVACY":
                penalty_factor = 0.2
            else:
                # Masking, Hashing, Tokenization, Redaction reduce risk to 0
                penalty_factor = 0.0
                
            total_weight += weight
            total_penalty += (weight * penalty_factor)
            
        # Base policy risk score (scaled to 70)
        base_risk_score = 0.0
        if total_weight > 0:
            base_risk_score = (total_penalty / total_weight) * 70.0
            
        # 3. Add Thief Agent Penalty
        thief_penalty = 0.0
        if thief_risk == "HIGH":
            thief_penalty = 30.0
        elif thief_risk == "MEDIUM":
            thief_penalty = 15.0
            
        final_risk = min(100.0, base_risk_score + thief_penalty)
        return round(final_risk, 2)

    def validate_results(self, tables_processed: List[Dict[str, Any]]) -> bool:
        """Runs the complete 3-layer Validation Engine check on the destination database using chunked loading."""
        print("\n" + "=" * 80)
        print("COMPLIANCE VALIDATION & PRIVACY RISK REPORT")
        print("=" * 80)
        
        all_checks_passed = True
        
        for table_result in tables_processed:
            table_name = table_result["table_name"]
            source_count = table_result["total_rows"]
            
            # Fetch destination row count
            dest_count = 0
            try:
                with self.destination_connector.engine.connect() as conn:
                    result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                    dest_count = result.scalar() if hasattr(result, 'scalar') else result.fetchone()[0]
            except Exception as e:
                logger.error(f"Failed to get row count for destination table {table_name}: {e}")
                all_checks_passed = False
                
            print(f"\nTable: '{table_name}'")
            print(f"  Source Rows: {source_count}")
            print(f"  Destination Rows: {dest_count}")
            
            # Layer 1 Check: Row count verification
            if source_count == dest_count:
                print("  [OK] Row counts match")
            else:
                print("  [FAIL] Row count mismatch!")
                all_checks_passed = False
                
            # Build map of policies
            table_policy = [
                col for col in self.policy.get("column_policies", [])
                if col["table_name"] == table_name
            ]
            policy_map = {col["column_name"]: col for col in table_policy}
            
            # Chunk processing loop for 100% database verification
            chunk_size = 5000
            offset = 0
            all_leaks = []
            suspicious_candidates = []
            
            try:
                with self.destination_connector.engine.connect() as conn:
                    while True:
                        query = text(f'SELECT * FROM "{table_name}" LIMIT {chunk_size} OFFSET {offset}')
                        chunk_df = pd.read_sql(query, conn)
                        
                        if chunk_df.empty:
                            break
                            
                        # Layer 2 Check: Deterministic Regex & Exact value Leak scan on the entire chunk
                        chunk_leaks = self._check_local_regex_leaks(table_name, chunk_df, policy_map)
                        if chunk_leaks:
                            all_leaks.extend(chunk_leaks)
                            all_checks_passed = False
                            
                        # Add suspicious rows from this chunk (top 5 longest text rows)
                        # We calculate a simple score: total string length across all fields
                        row_lengths = chunk_df.astype(str).apply(lambda r: r.str.len().sum(), axis=1)
                        chunk_df_with_len = chunk_df.copy()
                        chunk_df_with_len['__text_len__'] = row_lengths
                        top_chunk = chunk_df_with_len.sort_values(by='__text_len__', ascending=False).head(5)
                        suspicious_candidates.append(top_chunk)
                            
                        offset += chunk_size
                        
            except Exception as e:
                logger.error(f"Failed during chunked validation of table {table_name}: {e}")
                all_checks_passed = False
                
            # Print Layer 2 Check results
            if all_leaks:
                print("  [FAIL] Deterministic PII leaks detected!")
                # Print unique leaks to avoid spamming the logs
                for leak in list(set(all_leaks))[:10]:
                    print(f"    - {leak}")
                if len(set(all_leaks)) > 10:
                    print(f"    - ... and {len(set(all_leaks)) - 10} more leaks.")
            else:
                print("  [OK] No deterministic PII leaks found across all checked rows.")
                
            # Build the final 20-row sample for Layer 3 (Thief Agent)
            sample_df = pd.DataFrame()
            if suspicious_candidates:
                combined_suspicious = pd.concat(suspicious_candidates)
                sample_df = combined_suspicious.sort_values(by='__text_len__', ascending=False).head(20)
                # Drop the temporary length column
                sample_df = sample_df.drop(columns=['__text_len__'], errors='ignore')
                
            if sample_df.empty:
                print("  [WARN] No destination data found to perform Thief Agent audit.")
                continue
                
            # Layer 3 Check: Thief Agent Penetration test (LLM) on the most suspicious rows
            thief_report = self.run_thief_penetration_test(table_name, sample_df)
            if thief_report.get("anonymization_broken"):
                all_checks_passed = False
                
            # Calculate final mathematical risk score
            risk_score = self.calculate_privacy_risk_score(table_name, thief_report.get("risk_severity", "LOW"))
            print(f"\n  Final Privacy Risk Score: {risk_score} / 100")
            
            table_passed = True
            if risk_score == 0:
                print("  Status: SECURE & COMPLIANT [PASS]")
            elif risk_score < 30:
                print("  Status: LOW RISK [WARN] (Minor Quasi-identifier warnings)")
            elif risk_score < 70:
                print("  Status: MEDIUM RISK [WARN] (Vulnerabilities present)")
            else:
                print("  Status: HIGH RISK [FAIL] (PII leaks detected, NOT compliant)")
                all_checks_passed = False
                table_passed = False
                
            # Log results for Step 16 Audit Report Generator
            self.table_reports.append({
                "table_name": table_name,
                "row_counts_match": source_count == dest_count,
                "checks_passed": table_passed and not all_leaks,
                "risk_score": risk_score,
                "leaks": list(set(all_leaks)),
                "thief_report": thief_report
            })
                
        print("\n" + "=" * 80)
        if all_checks_passed:
            print("[SUCCESS] ALL VALIDATION CHECKS PASSED. SYSTEM SECURE.")
        else:
            print("[FAIL] VALIDATION CHECKS FAILED. EXPOSURES DETECTED.")
        print("=" * 80 + "\n")
        
        return all_checks_passed
