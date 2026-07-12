"""
LLM-based PII detection for context-aware identification.
Primary layer for intelligent PII detection.
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import logging

from llm_client import LLMClient

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LLMPIIDetection:
    """Represents LLM-based PII detection result."""
    column_name: str
    is_pii: bool
    pii_type: Optional[str]
    confidence: float
    recommended_technique: Optional[str]
    reasoning: Optional[str]


class LLMPiiDetector:
    """LLM-based PII detector using Claude or OpenAI API."""
    
    def __init__(self, provider: str = "github", model: str = None):
        """
        Initialize LLM detector with fallback support.
        
        Args:
            provider: Must be 'github' (only GitHub models supported)
            model: Specific model name (for GitHub Models). 
                   If None, uses default for provider.
                   GitHub defaults to 'gpt-4o'
        """
        if provider != "github":
            raise ValueError("Only GitHub models are supported. Provider must be 'github'.")
        
        self.provider = provider
        self.model = model or self._get_default_model()
        self.llm_client = LLMClient(provider=provider, model=model)
    
    def _get_default_model(self) -> str:
        """Get default model."""
        return os.getenv("LLM_MODEL", "gpt-4o")
    
    def _clean_json_response(self, response_text: str) -> str:
        """
        Clean LLM response to extract JSON content.
        
        Handles markdown code blocks and other formatting issues.
        
        Args:
            response_text: Raw response text from LLM
        
        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        return response_text
    
    def _create_detection_prompt(
        self,
        column_name: str,
        data_type: str,
        sample_values: List[str],
        table_name: Optional[str] = None,
        enterprise_type: str = "GENERAL",
        compliance_law: str = "DPDP Act 2023",
        enterprise_confidence: float = 0.5
    ) -> str:
        """
        Create a prompt for PII detection with enterprise context.
        
        Args:
            column_name: Name of the column to analyze
            data_type: SQL data type of the column
            sample_values: List of sample values from the column
            table_name: Optional table name for context
            enterprise_type: Enterprise type (BANKING, HEALTHCARE, HR, etc.)
            compliance_law: Applicable compliance law
            enterprise_confidence: Confidence in enterprise detection (0.0 to 1.0)
            
        Returns:
            Formatted prompt string
        """
        samples_str = "\n".join([f"  - {val}" for val in sample_values[:10]])
        
        prompt = f"""You are a PII (Personally Identifiable Information) detection expert 
for Indian {enterprise_type} enterprises.
Applicable compliance: {compliance_law}

=== CONTEXT ===
This is a {enterprise_type} database.
Enterprise detection confidence: {enterprise_confidence}
Every PII decision must consider {enterprise_type} regulations and sensitivity levels.

=== FEW-SHOT EXAMPLES ===

Example 1 — Clear Indian government ID:
Column: aadhaar_number | Table: customers | Type: VARCHAR(14)
Samples: ['4521 8834 9021', '5192 8374 6102', '6283 XXXX XXXX']
Answer:
{{
  "column_name": "aadhaar_number",
  "is_pii": true,
  "pii_type": "AADHAAR",
  "confidence": 0.99,
  "recommended_technique": "MASKING",
  "reasoning": "12-digit Aadhaar format confirmed by pattern and column name"
}}

Example 2 — Ambiguous column name, clear value pattern:
Column: emp_contact | Table: employees | Type: VARCHAR(15)
Samples: ['+91 9876543210', '919123456789', '9876543210']
Answer:
{{
  "column_name": "emp_contact",
  "is_pii": true,
  "pii_type": "INDIAN_PHONE",
  "confidence": 0.95,
  "recommended_technique": "TOKENIZATION",
  "reasoning": "Indian phone format detected from values despite ambiguous column name"
}}

Example 3 — Financial sensitive data (DPDP Act):
Column: monthly_salary | Table: employees | Type: DECIMAL
Samples: ['45000', '78000', '92000', '120000']
Answer:
{{
  "column_name": "monthly_salary",
  "is_pii": true,
  "pii_type": "FINANCIAL",
  "confidence": 0.90,
  "recommended_technique": "DIFFERENTIAL_PRIVACY",
  "reasoning": "Salary is sensitive financial data protected under DPDP Act 2023 Section 2(t)"
}}

Example 4 — Sensitive but no fixed pattern:
Column: date_of_birth | Table: customers | Type: DATE
Samples: ['1990-05-15', '1985-11-22', '1995-03-08']
Answer:
{{
  "column_name": "date_of_birth",
  "is_pii": true,
  "pii_type": "DATE_OF_BIRTH",
  "confidence": 0.95,
  "recommended_technique": "DIFFERENTIAL_PRIVACY",
  "reasoning": "Date of birth is personal data, noise shifts date by few days preserving realism"
}}

Example 5 — Non-PII correctly ignored:
Column: department | Table: employees | Type: VARCHAR(50)
Samples: ['Engineering', 'HR', 'Finance', 'Marketing']
Answer:
{{
  "column_name": "department",
  "is_pii": false,
  "pii_type": null,
  "confidence": 0.0,
  "recommended_technique": "NO_CHANGE",
  "reasoning": "Organizational category, not personal information"
}}

Example 6 — Enterprise-specific context matters:
Column: account_number | Table: accounts | Type: VARCHAR(18)
Enterprise: BANKING
Samples: ['XXXXXXXXXX3456', 'XXXXXXXXXX7890']
Answer:
{{
  "column_name": "account_number",
  "is_pii": true,
  "pii_type": "BANK_ACCOUNT",
  "confidence": 0.99,
  "recommended_technique": "MASKING",
  "reasoning": "Bank account number in financial institution — RBI guidelines require masking"
}}

=== ANONYMIZATION TECHNIQUES ===
- tokenization: Replace with realistic fake values (names, emails, phones)
- masking: Replace sensitive characters with X (aadhaar, pan, credit_card)
- hashing: One-way hash for IDs (user_id, customer_id)
- differential_privacy: Add statistical noise to numerical values (salary, age)
- no_change: Non-PII columns

=== PII TYPES TO DETECT ===

India-specific:
AADHAAR, PAN, INDIAN_PHONE, GSTIN,
INDIAN_PASSPORT, DRIVING_LICENSE, VOTER_ID, UAN

Global:
EMAIL, CREDIT_CARD, SSN, IP_ADDRESS,
FULL_NAME, ADDRESS, DATE_OF_BIRTH

Financial/Sensitive (DPDP Act 2023 Section 2(t)):
FINANCIAL — salary, balance, income,
            credit_score, transaction_amount,
            loan_amount, emi, bill_amount

Enterprise-specific:
BANK_ACCOUNT — bank account numbers
MEDICAL — diagnosis, blood_type, prescription
SUBSCRIBER — telecom subscriber details

=== COLUMN TO CLASSIFY ===

Table: {table_name or 'N/A'}
Enterprise: {enterprise_type}
Compliance: {compliance_law}
Column Name: {column_name}
Data Type: {data_type}

Sample Values:
{samples_str}

=== THINKING STEPS ===

For this column, before answering consider:
1. Does the column NAME suggest personal or sensitive data?
2. Do the sample VALUES match any known PII pattern?
3. Does the TABLE NAME add context about what this column represents?
4. Given this is a {enterprise_type} database, how sensitive is this column?
5. Which specific regulation ({compliance_law}) applies to this data type?
6. Is this financial/sensitive data under DPDP Act even if not directly identifiable?
7. When uncertain → flag as PII with lower confidence rather than missing it
8. Recommend appropriate technique based on PII type, enterprise context, and compliance requirements

=== STRICT RULES ===

CRITICAL — these rules must never be violated:
1. If is_pii is true → pii_type must NEVER be null or NONE
2. If type is unclear but column seems sensitive → use pii_type: UNKNOWN
3. Financial data (salary, balance, amounts) → always is_pii: true, type: FINANCIAL
4. Dates of birth → always is_pii: true, type: DATE_OF_BIRTH
5. Location data (pincode, city, state, address) → always is_pii: true, type: ADDRESS
6. Choose technique based on PII type, enterprise context, and compliance requirements
7. If technique is unclear → use MASKING as safest default
8. Confidence 0.0 means LLM failed — never use 0.0 for a real detection

=== RESPONSE FORMAT ===

Respond in JSON only, no extra text:
{{
    "column_name": "{column_name}",
    "is_pii": true/false,
    "pii_type": "TYPE or null",
    "confidence": 0.1 to 1.0,
    "recommended_technique": "TECHNIQUE or NO_CHANGE",
    "reasoning": "one clear sentence explaining the decision"
}}"""

        return prompt
    
    def detect_column(
        self,
        column_name: str,
        data_type: str,
        sample_values: List[str],
        table_name: Optional[str] = None,
        enterprise_type: str = "GENERAL",
        compliance_law: str = "DPDP Act 2023",
        enterprise_confidence: float = 0.5
    ) -> LLMPIIDetection:
        """
        Detect PII in a database column using LLM.
        
        Args:
            column_name: Name of the column to analyze
            data_type: SQL data type of the column
            sample_values: List of sample values from the column
            table_name: Optional table name for context
            enterprise_type: Enterprise type (BANKING, HEALTHCARE, HR, etc.)
            compliance_law: Applicable compliance law
            enterprise_confidence: Confidence in enterprise detection (0.0 to 1.0)
            
        Returns:
            LLMPIIDetection object with detection results
        """
        prompt = self._create_detection_prompt(column_name, data_type, sample_values, table_name, enterprise_type, compliance_law, enterprise_confidence)
        
        try:
            # Use LLMClient with automatic fallback
            response_text = self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024
            )
            
            # Log which model was used
            provider, model = self.llm_client.get_current_model()
            logger.info(f"PII detection for {column_name} used: {provider}/{model}")
            
            # Parse JSON response using helper method
            response_text = self._clean_json_response(response_text)
            result = json.loads(response_text)
            
            return LLMPIIDetection(
                column_name=column_name,
                is_pii=result.get("is_pii", False),
                pii_type=result.get("pii_type"),
                confidence=result.get("confidence", 0.0),
                recommended_technique=result.get("recommended_technique"),
                reasoning=result.get("reasoning")
            )
            
        except Exception as e:
            # Fallback to conservative detection if LLM fails
            # CRITICAL: Return is_pii=True to be safe - better to over-detect than miss PII
            print(f"LLM detection failed for {column_name}: {e}")
            return LLMPIIDetection(
                column_name=column_name,
                is_pii=True,  # Conservative: flag as PII if detection fails
                pii_type="unknown",
                confidence=0.0,  # Zero confidence due to uncertainty
                recommended_technique="tokenization",  # Default to reversible technique
                reasoning=f"LLM detection failed: {str(e)}. Conservative fallback: flagged as PII"
            )
    
    def detect_multiple_columns(
        self,
        columns: List[Dict[str, Any]]
    ) -> List[LLMPIIDetection]:
        """
        Detect PII in multiple columns (one API call per column).
        
        Args:
            columns: List of dicts with keys: column_name, data_type, sample_values, table_name (optional)
            
        Returns:
            List of LLMPIIDetection objects
        """
        results = []
        for col in columns:
            result = self.detect_column(
                column_name=col["column_name"],
                data_type=col["data_type"],
                sample_values=col["sample_values"],
                table_name=col.get("table_name")
            )
            results.append(result)
        return results
    
    def detect_table_columns_batch(
        self,
        table_name: str,
        columns: List[Dict[str, Any]],
        enterprise_type: str = "GENERAL",
        compliance_law: str = "DPDP Act 2023",
        enterprise_confidence: float = 0.5
    ) -> List[LLMPIIDetection]:
        """
        Detect PII in all columns of a table in a single API call.
        
        Args:
            table_name: Name of the table
            columns: List of dicts with keys: column_name, data_type, sample_values
            enterprise_type: Enterprise type (BANKING, HEALTHCARE, HR, etc.)
            compliance_law: Applicable compliance law
            enterprise_confidence: Confidence in enterprise detection (0.0 to 1.0)
            
        Returns:
            List of LLMPIIDetection objects
        """
        # Create a batch prompt for all columns
        columns_info = []
        for col in columns:
            samples_str = "\n".join([f"  - {val}" for val in col["sample_values"][:5]])
            columns_info.append(f"""
---
Column: {col['column_name']}
Data Type: {col['data_type']}
Sample Values:
{samples_str}
""")
        
        prompt = f"""You are a PII (Personally Identifiable Information) detection expert 
for Indian {enterprise_type} enterprises.
Applicable compliance: {compliance_law}

=== CONTEXT ===
This is a {enterprise_type} database.
Enterprise detection confidence: {enterprise_confidence}
Every PII decision must consider {enterprise_type} regulations and sensitivity levels.

=== COLUMNS TO CLASSIFY ===

Table: {table_name}
Enterprise: {enterprise_type}
Compliance: {compliance_law}

{"".join(columns_info)}

=== ANONYMIZATION TECHNIQUES ===
- tokenization: Replace with realistic fake values (names, emails, phones)
- masking: Replace sensitive characters with X (aadhaar, pan, credit_card)
- hashing: One-way hash for IDs (user_id, customer_id)
- differential_privacy: Add statistical noise to numerical values (salary, age)
- no_change: Non-PII columns

=== PII TYPES TO DETECT ===

India-specific:
AADHAAR, PAN, INDIAN_PHONE, GSTIN,
INDIAN_PASSPORT, DRIVING_LICENSE, VOTER_ID, UAN

Global:
EMAIL, CREDIT_CARD, SSN, IP_ADDRESS,
FULL_NAME, ADDRESS, DATE_OF_BIRTH

Financial/Sensitive (DPDP Act 2023 Section 2(t)):
FINANCIAL — salary, balance, income,
            credit_score, transaction_amount,
            loan_amount, emi, bill_amount

Enterprise-specific:
BANK_ACCOUNT — bank account numbers
MEDICAL — diagnosis, blood_type, prescription
SUBSCRIBER — telecom subscriber details

=== THINKING STEPS ===

For each column, before answering consider:
1. Does the column NAME suggest personal or sensitive data?
2. Do the sample VALUES match any known PII pattern?
3. Does the TABLE NAME add context about what this column represents?
4. Given this is a {enterprise_type} database, how sensitive is this column?
5. Which specific regulation ({compliance_law}) applies to this data type?
6. Is this financial/sensitive data under DPDP Act even if not directly identifiable?
7. When uncertain → flag as PII with lower confidence rather than missing it
8. Recommend appropriate technique based on PII type, enterprise context, and compliance requirements

=== STRICT RULES ===

CRITICAL — these rules must never be violated:
1. If is_pii is true → pii_type must NEVER be null or NONE
2. If type is unclear but column seems sensitive → use pii_type: UNKNOWN
3. Financial data (salary, balance, amounts) → always is_pii: true, type: FINANCIAL
4. Dates of birth → always is_pii: true, type: DATE_OF_BIRTH
5. Location data (pincode, city, state, address) → always is_pii: true, type: ADDRESS
6. Choose technique based on PII type, enterprise context, and compliance requirements
7. If technique is unclear → use MASKING as safest default
8. Confidence 0.0 means LLM failed — never use 0.0 for a real detection

=== RESPONSE FORMAT ===

Return a JSON array with one object per column, in the same order as the columns above.
No extra text, no markdown, no explanation outside JSON.

[
  {{
    "column_name": "column_name_here",
    "is_pii": true/false,
    "pii_type": "TYPE or null",
    "confidence": 0.1 to 1.0,
    "recommended_technique": "TECHNIQUE or NO_CHANGE",
    "reasoning": "one clear sentence explaining the decision"
  }}
]
"""
        
        try:
            # Use LLMClient with automatic fallback
            response_text = self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048
            )
            
            # Log which model was used
            provider, model = self.llm_client.get_current_model()
            logger.info(f"Batch PII detection for {table_name} used: {provider}/{model}")
            
            # Parse JSON response using helper method
            response_text = self._clean_json_response(response_text)
            results_array = json.loads(response_text)
            
            # Convert to LLMPIIDetection objects
            results = []
            for i, col in enumerate(columns):
                if i < len(results_array):
                    result_data = results_array[i]
                    results.append(LLMPIIDetection(
                        column_name=col["column_name"],
                        is_pii=result_data.get("is_pii", False),
                        pii_type=result_data.get("pii_type"),
                        confidence=result_data.get("confidence", 0.0),
                        recommended_technique=result_data.get("recommended_technique"),
                        reasoning=result_data.get("reasoning")
                    ))
                else:
                    # Fallback if LLM didn't return result for this column
                    results.append(LLMPIIDetection(
                        column_name=col["column_name"],
                        is_pii=True,
                        pii_type="unknown",
                        confidence=0.0,
                        recommended_technique="tokenization",
                        reasoning="Batch processing incomplete - conservative fallback"
                    ))
            
            return results
            
        except Exception as e:
            # Fallback to individual column detection if batch fails
            print(f"Batch detection failed for table {table_name}: {e}. Falling back to individual column detection.")
            return self.detect_multiple_columns(columns)


def detect_pii_with_llm(
    column_name: str,
    data_type: str,
    sample_values: List[str],
    table_name: Optional[str] = None,
    provider: str = "anthropic",
    model: str = None
) -> Dict[str, Any]:
    """
    Convenience function for single column PII detection.
    
    Args:
        column_name: Name of the column to analyze
        data_type: SQL data type of the column
        sample_values: List of sample values from the column
        table_name: Optional table name for context
        provider: 'anthropic', 'openai', or 'github'
        model: Specific model name (for GitHub Models). 
               If None, uses default for provider.
               GitHub defaults to 'gpt-4o'
        
    Returns:
        Dictionary with detection results
    """
    detector = LLMPiiDetector(provider=provider, model=model)
    result = detector.detect_column(column_name, data_type, sample_values, table_name)
    
    return {
        "column_name": result.column_name,
        "is_pii": result.is_pii,
        "pii_type": result.pii_type,
        "confidence": result.confidence,
        "recommended_technique": result.recommended_technique,
        "reasoning": result.reasoning,
        "detection_method": "llm",
        "model_used": detector.model,
        "provider_used": detector.provider
    }


if __name__ == "__main__":
    # Test with sample data
    print("LLM-based PII Detection Test")
    print("=" * 60)
    
    # Sample column data
    test_columns = [
        {
            "column_name": "customer_aadhaar",
            "data_type": "VARCHAR(12)",
            "sample_values": ["1234 5678 9012", "2345-6789-0123", "345678901234"],
            "table_name": "customers"
        },
        {
            "column_name": "emp_contact",
            "data_type": "VARCHAR(15)",
            "sample_values": ["+91 9876543210", "919876543210", "9876543210"],
            "table_name": "employees"
        },
        {
            "column_name": "pan_number",
            "data_type": "VARCHAR(10)",
            "sample_values": ["ABCDE1234F", "FGHIJ5678K", "LMNOP9012Q"],
            "table_name": "kyc_details"
        },
        {
            "column_name": "user_email",
            "data_type": "VARCHAR(100)",
            "sample_values": ["user@example.com", "test@test.org", "admin@company.in"],
            "table_name": "users"
        },
        {
            "column_name": "product_name",
            "data_type": "VARCHAR(50)",
            "sample_values": ["Laptop", "Mouse", "Keyboard"],
            "table_name": "products"
        }
    ]
    
    print("Note: This test requires API keys in .env file")
    print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY to run actual tests")
    print("\nTo run:")
    print("1. Copy .env.example to .env")
    print("2. Add your API key")
    print("3. Run: python llm_pii_detection.py")
