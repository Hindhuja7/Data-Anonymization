"""
India-specific PII regex patterns for detection.
Primary layer for Indian PII formats.
"""

import re
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PatternMatch:
    """Represents a regex match result."""
    pattern_name: str
    matched_value: str
    confidence: float


class IndiaPIIPatterns:
    """India-specific PII detection patterns."""
    
    # Aadhaar: 12 digits, optionally formatted with spaces or hyphens
    # Format: XXXX XXXX XXXX or XXXX-XXXX-XXXX or XXXXXXXXXXXX
    AADHAAR_PATTERN = re.compile(
        r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
    )
    
    # PAN: 10 characters - 5 letters + 4 digits + 1 letter
    # Format: ABCDE1234F
    PAN_PATTERN = re.compile(
        r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b',
        re.IGNORECASE
    )
    
    # Indian Phone: +91 followed by 10 digits, or 10 digits starting with 6-9
    # Formats: +91 9876543210, +91-9876543210, 919876543210, 9876543210
    INDIAN_PHONE_PATTERN = re.compile(
        r'\b(\+91[-\s]?|91)?[6-9]\d{9}\b'
    )
    
    # GSTIN: 15 characters - 2 digits (state code) + PAN + 1 digit + 1 letter + 1 digit
    # Format: 22ABCDE1234F1Z5 or 07ABCDE1234F1Z5
    GSTIN_PATTERN = re.compile(
        r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b',
        re.IGNORECASE
    )
    
    # Indian Passport: 8 characters - 1 letter + 7 digits
    # Format: A1234567
    INDIAN_PASSPORT_PATTERN = re.compile(
        r'\b[A-Z]{1}[0-9]{7}\b',
        re.IGNORECASE
    )
    
    # Driving License: State-specific formats (varies by state)
    # Common format: 2 letters (state code) + 2 digits (RTO code) + rest alphanumeric
    # Example: MH12AB1234, DL-01-2023001234
    DRIVING_LICENSE_PATTERN = re.compile(
        r'\b[A-Z]{2}[0-9]{2}[A-Z0-9]+|DL[-\s]?[0-9]{2}[-\s]?[0-9]{11}\b',
        re.IGNORECASE
    )
    
    # Voter ID (EPIC): 10 alphanumeric characters (typically 3 letters + 7 digits)
    # Format: ABC1234567
    VOTER_ID_PATTERN = re.compile(
        r'\b[A-Z]{3}[0-9]{7}\b',
        re.IGNORECASE
    )
    
    # UAN (Universal Account Number): 12 digits
    # Format: 123456789012
    UAN_PATTERN = re.compile(
        r'\b\d{12}\b'
    )
    
    @classmethod
    def detect_aadhaar(cls, value: str) -> Optional[PatternMatch]:
        """Detect Aadhaar number."""
        cleaned = value.replace(' ', '').replace('-', '')
        if cls.AADHAAR_PATTERN.fullmatch(value) or (len(cleaned) == 12 and cleaned.isdigit()):
            return PatternMatch(
                pattern_name="aadhaar",
                matched_value=value,
                confidence=0.95
            )
        return None
    
    @classmethod
    def detect_pan(cls, value: str) -> Optional[PatternMatch]:
        """Detect PAN number."""
        if cls.PAN_PATTERN.fullmatch(value.upper()):
            return PatternMatch(
                pattern_name="pan",
                matched_value=value,
                confidence=0.98
            )
        return None
    
    @classmethod
    def detect_indian_phone(cls, value: str) -> Optional[PatternMatch]:
        """Detect Indian phone number."""
        cleaned = value.replace(' ', '').replace('-', '')
        # Use search instead of fullmatch since pattern has \b boundaries
        # and cleaned string won't have word boundaries
        if cls.INDIAN_PHONE_PATTERN.search(cleaned):
            return PatternMatch(
                pattern_name="indian_phone",
                matched_value=value,
                confidence=0.90
            )
        return None
    
    @classmethod
    def detect_gstin(cls, value: str) -> Optional[PatternMatch]:
        """Detect GSTIN."""
        if cls.GSTIN_PATTERN.fullmatch(value.upper()):
            return PatternMatch(
                pattern_name="gstin",
                matched_value=value,
                confidence=0.95
            )
        return None
    
    @classmethod
    def detect_indian_passport(cls, value: str) -> Optional[PatternMatch]:
        """Detect Indian passport number."""
        if cls.INDIAN_PASSPORT_PATTERN.fullmatch(value.upper()):
            return PatternMatch(
                pattern_name="indian_passport",
                matched_value=value,
                confidence=0.60  # Lowered from 0.85 - pattern is too generic (1 letter + 7 digits)
            )
        return None
    
    @classmethod
    def detect_driving_license(cls, value: str) -> Optional[PatternMatch]:
        """Detect driving license number."""
        if cls.DRIVING_LICENSE_PATTERN.fullmatch(value.upper()):
            return PatternMatch(
                pattern_name="driving_license",
                matched_value=value,
                confidence=0.75
            )
        return None
    
    @classmethod
    def detect_voter_id(cls, value: str) -> Optional[PatternMatch]:
        """Detect voter ID (EPIC)."""
        if cls.VOTER_ID_PATTERN.fullmatch(value.upper()):
            return PatternMatch(
                pattern_name="voter_id",
                matched_value=value,
                confidence=0.80
            )
        return None
    
    @classmethod
    def detect_uan(cls, value: str) -> Optional[PatternMatch]:
        """Detect UAN (Universal Account Number)."""
        if cls.UAN_PATTERN.fullmatch(value):
            return PatternMatch(
                pattern_name="uan",
                matched_value=value,
                confidence=0.85
            )
        return None
    
    @classmethod
    def detect_all(cls, value: str, column_name: str = None) -> list[PatternMatch]:
        """
        Run all India-specific PII detection patterns on a value.
        
        Args:
            value: The value to check for PII
            column_name: Optional column name for context-aware disambiguation
                         (e.g., helps distinguish Aadhaar vs UAN which both match 12 digits)
        """
        if not isinstance(value, str):
            value = str(value) if value is not None else ""

        matches = []
        
        detectors = [
            cls.detect_aadhaar,
            cls.detect_pan,
            cls.detect_indian_phone,
            cls.detect_gstin,
            cls.detect_indian_passport,
            cls.detect_driving_license,
            cls.detect_voter_id,
            cls.detect_uan,
        ]
        
        for detector in detectors:
            match = detector(value)
            if match:
                # Adjust confidence based on column name context
                if column_name:
                    column_lower = column_name.lower()
                    
                    # Boost Aadhaar confidence if column name suggests Aadhaar
                    if match.pattern_name == "aadhaar" and any(
                        keyword in column_lower 
                        for keyword in ["aadhaar", "uid", "uidai"]
                    ):
                        match = PatternMatch(
                            pattern_name=match.pattern_name,
                            matched_value=match.matched_value,
                            confidence=min(0.99, match.confidence + 0.10)
                        )
                    
                    # Boost UAN confidence if column name suggests UAN
                    elif match.pattern_name == "uan" and any(
                        keyword in column_lower 
                        for keyword in ["uan", "epfo", "pf", "provident"]
                    ):
                        match = PatternMatch(
                            pattern_name=match.pattern_name,
                            matched_value=match.matched_value,
                            confidence=min(0.99, match.confidence + 0.10)
                        )
                    
                    # Penalize Aadhaar if column name suggests UAN
                    elif match.pattern_name == "aadhaar" and any(
                        keyword in column_lower 
                        for keyword in ["uan", "epfo", "pf", "provident"]
                    ):
                        match = PatternMatch(
                            pattern_name=match.pattern_name,
                            matched_value=match.matched_value,
                            confidence=max(0.0, match.confidence - 0.30)
                        )
                    
                    # Penalize UAN if column name suggests Aadhaar
                    elif match.pattern_name == "uan" and any(
                        keyword in column_lower 
                        for keyword in ["aadhaar", "uid", "uidai"]
                    ):
                        match = PatternMatch(
                            pattern_name=match.pattern_name,
                            matched_value=match.matched_value,
                            confidence=max(0.0, match.confidence - 0.30)
                        )
                
                matches.append(match)
        
        return matches


def detect_india_pii(value: str, column_name: str = None) -> Dict[str, any]:
    """
    Detect if a value contains India-specific PII.
    Returns a dictionary with detection results.
    
    Args:
        value: The value to check
        column_name: Optional column name for context
    """
    matches = IndiaPIIPatterns.detect_all(value, column_name=column_name)
    
    if not matches:
        return {
            "is_pii": False,
            "pii_type": None,
            "confidence": 0.0,
            "matched_value": None,
            "column_name": column_name,
            "source": "regex"
        }
    
    # Return the highest confidence match
    best_match = max(matches, key=lambda m: m.confidence)
    
    return {
        "is_pii": True,
        "pii_type": best_match.pattern_name,
        "confidence": best_match.confidence,
        "matched_value": best_match.matched_value,
        "column_name": column_name,
        "source": "regex"
    }


def detect_india_pii_column(
    column_name: str,
    data_type: str,
    sample_values: list[str],
    table_name: str = None
) -> Dict[str, any]:
    """
    Detect PII in a database column using India-specific regex patterns.
    Fully dynamic detection based on actual data patterns and column names.
    
    Args:
        column_name: Name of the column
        data_type: SQL data type of the column
        sample_values: List of sample values from the column
        table_name: Optional table name (for logging only, not used for assumptions)
    
    Returns:
        Dictionary with detection results
    """
    # Column name context for disambiguation (data-driven, not table-driven)
    column_context = {}
    if column_name:
        column_lower = column_name.lower()
        
        # Column name hints for PII type disambiguation
        if any(keyword in column_lower for keyword in ["aadhaar", "uid", "uidai"]):
            column_context = {"boost_pattern": "aadhaar", "confidence_adjust": 0.15}
        elif any(keyword in column_lower for keyword in ["pan", "permanent"]):
            column_context = {"boost_pattern": "pan", "confidence_adjust": 0.15}
        elif any(keyword in column_lower for keyword in ["phone", "mobile", "contact", "tel"]):
            column_context = {"boost_pattern": "indian_phone", "confidence_adjust": 0.15}
        elif any(keyword in column_lower for keyword in ["gstin", "gst"]):
            column_context = {"boost_pattern": "gstin", "confidence_adjust": 0.15}
        elif any(keyword in column_lower for keyword in ["passport"]):
            column_context = {"boost_pattern": "indian_passport", "confidence_adjust": 0.15}
        elif any(keyword in column_lower for keyword in ["license", "dl", "driving"]):
            column_context = {"boost_pattern": "driving_license", "confidence_adjust": 0.15}
        elif any(keyword in column_lower for keyword in ["voter", "epic"]):
            column_context = {"boost_pattern": "voter_id", "confidence_adjust": 0.15}
        elif any(keyword in column_lower for keyword in ["uan", "epfo", "pf", "provident"]):
            column_context = {"boost_pattern": "uan", "confidence_adjust": 0.15}
    
    # Check sample values for PII patterns
    all_matches = []
    for value in sample_values[:10]:  # Check first 10 samples
        matches = IndiaPIIPatterns.detect_all(value, column_name=column_name)
        
        # Apply column-specific confidence adjustments
        if column_context and matches:
            for match in matches:
                if match.pattern_name == column_context.get("boost_pattern"):
                    match = PatternMatch(
                        pattern_name=match.pattern_name,
                        matched_value=match.matched_value,
                        confidence=min(0.99, match.confidence + column_context.get("confidence_adjust", 0.0))
                    )
        
        all_matches.extend(matches)
    
    if not all_matches:
        return {
            "is_pii": False,
            "pii_type": None,
            "confidence": 0.0,
            "recommended_technique": None,
            "reasoning": f"No India-specific PII patterns detected in sample values for column '{column_name}'",
            "column_name": column_name,
            "table_name": table_name,
            "source": "regex"
        }
    
    # Find the most common PII type among matches
    from collections import Counter
    pii_type_counts = Counter(match.pattern_name for match in all_matches)
    most_common_pii_type = pii_type_counts.most_common(1)[0][0]
    
    # Get average confidence for this PII type
    type_matches = [m for m in all_matches if m.pattern_name == most_common_pii_type]
    avg_confidence = sum(m.confidence for m in type_matches) / len(type_matches)
    
    # Determine recommended technique based on PII type
    technique_map = {
        "aadhaar": "masking",
        "pan": "masking",
        "indian_phone": "tokenization",
        "gstin": "masking",
        "indian_passport": "masking",
        "driving_license": "masking",
        "voter_id": "masking",
        "uan": "masking"
    }
    
    recommended_technique = technique_map.get(most_common_pii_type, "tokenization")
    
    # Dynamic reasoning based on actual data patterns
    column_hint = f" (column name suggests {column_context.get('boost_pattern')})" if column_context else ""
    
    return {
        "is_pii": True,
        "pii_type": most_common_pii_type,
        "confidence": avg_confidence,
        "recommended_technique": recommended_technique,
        "reasoning": f"Detected {most_common_pii_type} in {len(type_matches)}/{len(sample_values[:10])} sample values using India-specific regex patterns.{column_hint}",
        "column_name": column_name,
        "table_name": table_name,
        "source": "regex"
    }


if __name__ == "__main__":
    # Test the patterns
    test_values = [
        "1234 5678 9012",  # Aadhaar
        "1234-5678-9012",  # Aadhaar with hyphens
        "123456789012",    # Aadhaar without formatting
        "ABCDE1234F",      # PAN
        "abcde1234f",      # PAN lowercase
        "+91 9876543210",  # Indian phone with +91
        "919876543210",    # Indian phone with 91 prefix
        "9876543210",      # Indian phone without prefix
        "22ABCDE1234F1Z5", # GSTIN
        "A1234567",        # Indian passport
        "MH12AB1234",      # Driving license
        "DL-01-2023001234", # Driving license alternative format
        "ABC1234567",      # Voter ID
        "123456789012",    # UAN
        "not_pii_value",   # Non-PII
    ]
    
    print("India PII Detection Test Results:")
    print("=" * 60)
    for value in test_values:
        result = detect_india_pii(value)
        print(f"Value: {value:25} | PII: {result['is_pii']:5} | Type: {result['pii_type'] or 'N/A':20} | Confidence: {result['confidence']}")
