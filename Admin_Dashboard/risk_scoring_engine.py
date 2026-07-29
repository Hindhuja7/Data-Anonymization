"""
Authoritative Risk Scoring Engine for DataVault AI
Calculates exact policy risk scores, privacy scores, and vulnerabilities.
"""

from typing import Dict, List, Any

class RiskScoringEngine:
    """Authoritative backend Risk Scoring Engine for DataVault AI."""
    
    def calculate_policy_risk(self, column_policies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate authoritative risk score and privacy score for a given column policy set.
        
        Formula Contract:
        - Each un-anonymized direct PII column (email, phone, aadhaar, pan, ssn, card) under NO_CHANGE adds 25.0 risk points.
        - Each un-anonymized quasi-identifier (dob, location, salary) under NO_CHANGE adds 15.0 risk points.
        - risk_score: min(100.0, total_penalties)
        - privacy_score: max(0.0, 100.0 - risk_score)
        - risk_level: LOW (0.0), MEDIUM (0.1 - 49.9), HIGH (50.0 - 100.0)
        """
        if not column_policies:
            return {
                "policy_risk_score": 0.0,
                "privacy_score": 100.0,
                "risk_level": "LOW",
                "vulnerabilities": []
            }
            
        risk_score = 0.0
        vulnerabilities = []
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
            
            # Direct or Quasi PII left as NO_CHANGE creates un-anonymized risk
            if technique == "NO_CHANGE":
                if is_direct_pii:
                    raw_direct_pii_count += 1
                    risk_score += 25.0
                    vulnerabilities.append(f"CRITICAL: Direct PII column '{table_name}.{col_name}' ({pii_type or col_name}) left un-anonymized (NO_CHANGE).")
                elif is_quasi_pii or is_pii_flag:
                    raw_quasi_pii_count += 1
                    risk_score += 15.0
                    vulnerabilities.append(f"WARNING: Quasi-identifier column '{table_name}.{col_name}' left un-anonymized (NO_CHANGE).")
            elif technique == "DIFFERENTIAL_PRIVACY":
                risk_score += 2.0
                
        if raw_quasi_pii_count >= 2:
            risk_score += 10.0
            vulnerabilities.append("High linkage attack risk: Multiple quasi-identifiers left unprotected.")
            
        final_risk_score = round(min(100.0, max(0.0, risk_score)), 1)
        final_privacy_score = round(max(0.0, 100.0 - final_risk_score), 1)
        
        if final_risk_score == 0.0:
            risk_level = "LOW"
        elif final_risk_score < 50.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
            
        return {
            "policy_risk_score": final_risk_score,
            "privacy_score": final_privacy_score,
            "risk_level": risk_level,
            "vulnerabilities": vulnerabilities
        }
