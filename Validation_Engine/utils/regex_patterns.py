"""
Centralized regex pattern definitions for Indian & International PII types.
"""

from typing import Dict

PII_REGEX_PATTERNS: Dict[str, str] = {
    "AADHAAR": r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b",
    "PAN": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "PHONE": r"\b(?:\+?91)?[ -]?[6-9]\d{4}[ -]?\d{5}\b",
    "GSTIN": r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b"
}
