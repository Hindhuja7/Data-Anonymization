"""
Post-processing PrivacyScoreCalculator module.
Calculates mathematical Risk Score and Privacy Score from ValidationResult[] without calling validator internals.
"""

from typing import List, Dict, Tuple, Any
from base_validator import ValidationResult, ValidationStatus, FindingSeverity

class PrivacyScoreCalculator:
    """Post-processor deriving mathematical Privacy and Risk Scores from diagnostic ValidationResults."""

    @staticmethod
    def calculate_scores(results: List[ValidationResult]) -> Tuple[int, float]:
        """
        Derives (privacy_score, risk_score).
        Privacy Score ranges 0-100.
        Risk Score ranges 0.0 - 100.0.
        """
        base_risk = 0.0
        
        for res in results:
            if res.status == ValidationStatus.FAIL:
                base_risk += 25.0
            elif res.status == ValidationStatus.WARNING:
                base_risk += 10.0

            for finding in res.findings:
                if finding.severity == FindingSeverity.CRITICAL:
                    base_risk += 15.0
                elif finding.severity == FindingSeverity.HIGH:
                    base_risk += 8.0
                elif finding.severity == FindingSeverity.MEDIUM:
                    base_risk += 3.0
                elif finding.severity == FindingSeverity.LOW:
                    base_risk += 1.0

        # Cap risk score between 0.5 and 100.0 (default 1.5 if clean pass)
        risk_score = round(min(max(base_risk, 1.5), 100.0), 1)
        privacy_score = int(round(100.0 - risk_score))
        
        return max(privacy_score, 0), risk_score
