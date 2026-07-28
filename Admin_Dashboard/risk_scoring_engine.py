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
        - risk_score: 0.0 (perfectly anonymized) to 100.0 (raw high-risk PII leaks)
        - privacy_score: max(0.0, 100.0 - risk_score)
        - risk_level: LOW (risk == 0.0), MEDIUM (0.0 < risk < 70.0), HIGH (risk >= 70.0)
        """
        if not column_policies:
            return {
                "policy_risk_score": 0.0,
                "privacy_score": 100.0,
                "risk_level": "LOW",
                "vulnerabilities": []
            }
            
        total_weight = 0.0
        total_penalty = 0.0
        vulnerabilities = []
        
        for col in column_policies:
            pii_type = col.get("pii_type", "NONE")
            technique = col.get("anonymization_technique", "NO_CHANGE")
            col_name = col.get("column_name", "")
            table_name = col.get("table_name", "")
            
            if pii_type in ["IDENTIFIER", "NAME", "FULL_NAME", "EMAIL", "PHONE", "AADHAAR", "PAN", "GSTIN", "SSN", "CREDIT_CARD", "SENSITIVE"]:
                weight = 1.0
            elif pii_type in ["QUASI_IDENTIFIER", "DOB", "DATE_OF_BIRTH", "AGE", "GENDER", "LOCATION", "ADDRESS", "SALARY", "BALANCE", "FINANCIAL"]:
                weight = 0.5
            elif col.get("is_pii", False):
                weight = 0.5
            else:
                weight = 0.0
                
            if technique == "NO_CHANGE" and col.get("is_pii", False):
                penalty_factor = 1.0
                vulnerabilities.append(f"PII Column '{table_name}.{col_name}' left unanonymized (NO_CHANGE).")
            elif technique == "DIFFERENTIAL_PRIVACY":
                penalty_factor = 0.2
            else:
                penalty_factor = 0.0
                
            total_weight += weight
            total_penalty += (weight * penalty_factor)
            
        base_risk_score = 0.0
        if total_weight > 0:
            base_risk_score = (total_penalty / total_weight) * 70.0
            
        quasi_left_raw = any(
            c.get("pii_type") in ["QUASI_IDENTIFIER", "DOB", "AGE", "GENDER", "LOCATION", "SALARY", "BALANCE"] and 
            c.get("anonymization_technique") == "NO_CHANGE"
            for c in column_policies
        )
        thief_penalty = 15.0 if quasi_left_raw else 0.0
        if quasi_left_raw:
            vulnerabilities.append("Quasi-identifiers left raw might allow linkage attacks.")
            
        risk_score = round(min(100.0, base_risk_score + thief_penalty), 2)
        privacy_score = round(max(0.0, 100.0 - risk_score), 2)
        
        if risk_score == 0.0:
            risk_level = "LOW"
        elif risk_score < 70.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
            
        return {
            "policy_risk_score": risk_score,
            "privacy_score": privacy_score,
            "risk_level": risk_level,
            "vulnerabilities": vulnerabilities
        }
