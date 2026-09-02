"""
Authoritative Risk Scoring Engine for DataVault AI
Calculates exact policy risk scores, privacy scores, and vulnerabilities.
"""

from typing import Dict, List, Any

class RiskScoringEngine:
    """Authoritative backend Risk Scoring Engine for DataVault AI."""
    
    def calculate_policy_risk(self, column_policies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate authoritative risk score, raw intrinsic exposure, privacy score, and PII metrics for a given column policy set.
        """
        if not column_policies:
            return {
                "policy_risk_score": 0.0,
                "privacy_score": 100.0,
                "raw_intrinsic_risk": 0.0,
                "raw_intrinsic_privacy": 100.0,
                "raw_risk_level": "LOW",
                "risk_level": "LOW",
                "total_pii_columns": 0,
                "protected_pii_columns": 0,
                "vulnerabilities": []
            }
            
        active_risk_accum = 0.0
        raw_intrinsic_accum = 0.0
        vulnerabilities = []
        
        total_pii_count = 0
        protected_pii_count = 0
        raw_direct_pii_count = 0
        raw_quasi_pii_count = 0
        
        for col in column_policies:
            col_name = str(col.get("column_name", ""))
            table_name = str(col.get("table_name", ""))
            technique = str(col.get("anonymization_technique") or "NO_CHANGE").upper()
            pii_type = str(col.get("pii_type") or "").upper()
            is_pii_flag = bool(col.get("is_pii", False))
            
            col_lower = col_name.lower()
            is_direct_pii = (
                pii_type in ["EMAIL", "PHONE", "AADHAAR", "PAN", "GSTIN", "SSN", "CREDIT_CARD", "NAME", "FULL_NAME", "IDENTIFIER"] or
                any(k in col_lower for k in ["email", "phone", "mobile", "aadhaar", "pan", "ssn", "card", "credit_card"])
            )
            is_quasi_pii = (
                pii_type in ["QUASI_IDENTIFIER", "DOB", "DATE_OF_BIRTH", "AGE", "GENDER", "LOCATION", "ADDRESS", "SALARY", "BALANCE", "FINANCIAL"] or
                any(k in col_lower for k in ["dob", "birth", "address", "city", "state", "pincode", "zip", "salary", "balance", "amount"])
            )
            
            if is_direct_pii or is_quasi_pii or is_pii_flag:
                total_pii_count += 1
                if is_direct_pii:
                    raw_direct_pii_count += 1
                    raw_intrinsic_accum += 18.0
                elif is_quasi_pii or is_pii_flag:
                    raw_quasi_pii_count += 1
                    raw_intrinsic_accum += 10.0

                if technique == "NO_CHANGE":
                    if is_direct_pii:
                        active_risk_accum += 25.0
                        vulnerabilities.append(f"CRITICAL: Direct PII column '{table_name}.{col_name}' ({pii_type or col_name}) left un-anonymized (NO_CHANGE).")
                    else:
                        active_risk_accum += 15.0
                        vulnerabilities.append(f"WARNING: Quasi-identifier column '{table_name}.{col_name}' left un-anonymized (NO_CHANGE).")
                else:
                    protected_pii_count += 1
                    if technique == "MASKING":
                        active_risk_accum += 3.0
                    elif technique in ["GENERALIZATION", "NOISE"]:
                        active_risk_accum += 4.5
                    elif technique in ["TOKENIZATION"]:
                        active_risk_accum += 1.5
                    elif technique in ["HASHING", "HASH_SHA256"]:
                        active_risk_accum += 0.5
                    elif technique in ["DIFFERENTIAL_PRIVACY", "LAPLACE_DP"]:
                        active_risk_accum += 1.0
                    else:
                        active_risk_accum += 2.0
                
        if raw_quasi_pii_count >= 2:
            raw_intrinsic_accum += 8.0
            if protected_pii_count < total_pii_count:
                active_risk_accum += 8.0
                vulnerabilities.append("High linkage attack risk: Multiple quasi-identifiers left unprotected.")
            
        final_risk_score = round(min(100.0, max(0.0, active_risk_accum)), 1)
        final_privacy_score = round(max(0.0, 100.0 - final_risk_score), 1)
        
        final_intrinsic_risk = round(min(98.0, max(12.0, raw_intrinsic_accum)), 1)
        final_intrinsic_privacy = round(max(0.0, 100.0 - final_intrinsic_risk), 1)
        
        def _get_level(score: float) -> str:
            if score == 0.0: return "LOW"
            if score < 50.0: return "MEDIUM"
            return "HIGH"

        return {
            "policy_risk_score": final_risk_score,
            "privacy_score": final_privacy_score,
            "risk_level": _get_level(final_risk_score),
            "raw_intrinsic_risk": final_intrinsic_risk,
            "raw_intrinsic_privacy": final_intrinsic_privacy,
            "raw_risk_level": _get_level(final_intrinsic_risk),
            "total_pii_columns": total_pii_count,
            "protected_pii_columns": protected_pii_count,
            "vulnerabilities": vulnerabilities
        }
