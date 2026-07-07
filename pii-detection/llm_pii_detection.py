"""
LLM-based PII detection for context-aware identification.
Primary layer for intelligent PII detection.
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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
    
    # Available GitHub Models (all FREE)
    GITHUB_MODELS = {
        "gpt-4o": "GPT-4o (Best Quality)",
        "gpt-4o-mini": "GPT-4o Mini (Faster)",
        "llama-3.1-70b": "Llama 3.1 70B (Open Source)",
        "llama-3.1-8b": "Llama 3.1 8B (Fastest)",
        "mistral-7b": "Mistral 7B (Open Source)",
    }
    
    def __init__(self, provider: str = "anthropic", model: str = None):
        """
        Initialize LLM detector.
        
        Args:
            provider: 'anthropic', 'openai', or 'github' (for free GitHub Models)
            model: Specific model name (for GitHub Models). 
                   If None, uses default for provider.
                   GitHub defaults to 'gpt-4o'
        """
        self.provider = provider
        self.model = model
        
        if provider == "anthropic":
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
                self.model = model or "claude-3-sonnet-20240229"
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
                
        elif provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.model = model or "gpt-4"
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        
        elif provider == "github":
            # GitHub Models - Free tier using OpenAI SDK with custom base_url
            self.api_key = os.getenv("GITHUB_API_KEY")
            if not self.api_key:
                raise ValueError("GITHUB_API_KEY not found in environment variables")
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://models.inference.ai.azure.com"
                )
                # Default to gpt-4o if no model specified
                self.model = model or "gpt-4o"
                if self.model not in self.GITHUB_MODELS:
                    raise ValueError(f"Invalid GitHub model: {self.model}. Available: {list(self.GITHUB_MODELS.keys())}")
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        else:
            raise ValueError(f"Invalid provider: {provider}. Use 'anthropic', 'openai', or 'github'")
    
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
        table_name: Optional[str] = None
    ) -> str:
        """
        Create a prompt for PII detection.
        
        Args:
            column_name: Name of the column to analyze
            data_type: SQL data type of the column
            sample_values: List of sample values from the column
            table_name: Optional table name for context
            
        Returns:
            Formatted prompt string
        """
        samples_str = "\n".join([f"  - {val}" for val in sample_values[:10]])
        
        prompt = f"""You are a PII (Personally Identifiable Information) detection expert for Indian enterprises.

Analyze the following database column and determine if it contains PII:

Table Name: {table_name or 'N/A'}
Column Name: {column_name}
Data Type: {data_type}

Sample Values:
{samples_str}

PII Types to Detect:
- India-specific: aadhaar, pan, indian_phone, gstin, indian_passport, driving_license, voter_id, uan
- Global: email, credit_card, ssn, ip_address, url, generic_phone, full_name, address, date_of_birth

Anonymization Techniques:
- tokenization: Replace with realistic fake values (names, emails, phones)
- masking: Replace sensitive characters with X (aadhaar, pan, credit_card)
- hashing: One-way hash for IDs (user_id, customer_id)
- differential_privacy: Add statistical noise to numerical values (salary, age)
- no_change: Non-PII columns

Respond in JSON format only:
{{
    "is_pii": true/false,
    "pii_type": "type_name or null",
    "confidence": 0.0 to 1.0,
    "recommended_technique": "technique_name or null",
    "reasoning": "brief explanation"
}}

Consider:
1. Column name patterns (even if not exact, e.g., "emp_contact", "kyc_uid", "ref_no_2")
2. Data format and structure of sample values
3. Context from table name
4. Indian-specific formats (Aadhaar, PAN, +91 phone numbers)
5. Be conservative - if uncertain, flag as PII with lower confidence"""

        return prompt
    
    def detect_column(
        self,
        column_name: str,
        data_type: str,
        sample_values: List[str],
        table_name: Optional[str] = None
    ) -> LLMPIIDetection:
        """
        Detect PII in a database column using LLM.
        
        Args:
            column_name: Name of the column to analyze
            data_type: SQL data type of the column
            sample_values: List of sample values from the column
            table_name: Optional table name for context
            
        Returns:
            LLMPIIDetection object with detection results
        """
        prompt = self._create_detection_prompt(column_name, data_type, sample_values, table_name)
        
        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
                
            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1024
                )
                response_text = response.choices[0].message.content
            
            elif self.provider == "github":
                # GitHub Models - uses selected model via OpenAI SDK
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1024
                )
                response_text = response.choices[0].message.content
            
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
        columns: List[Dict[str, Any]]
    ) -> List[LLMPIIDetection]:
        """
        Detect PII in all columns of a table in a single API call.
        
        Args:
            table_name: Name of the table
            columns: List of dicts with keys: column_name, data_type, sample_values
            
        Returns:
            List of LLMPIIDetection objects
        """
        # Create a batch prompt for all columns
        columns_info = []
        for col in columns:
            samples_str = "\n".join([f"  - {val}" for val in col["sample_values"][:5]])
            columns_info.append(f"""
Column: {col['column_name']}
Data Type: {col['data_type']}
Sample Values:
{samples_str}
""")
        
        prompt = f"""You are a PII (Personally Identifiable Information) detection expert for Indian enterprises.

Analyze the following table and determine which columns contain PII:

Table Name: {table_name}

Columns:
{"".join(columns_info)}

For each column, provide a JSON response with:
- is_pii: boolean
- pii_type: one of [aadhaar, pan, indian_phone, gstin, passport, driving_license, voter_id, uan, email, full_name, address, credit_card, ssn, none]
- confidence: float (0.0 to 1.0)
- recommended_technique: one of [tokenization, masking, hashing, differential_privacy, no_change]
- reasoning: brief explanation

Return the results as a JSON array with one object per column, in the same order as the columns above.

Example format:
[
  {{
    "column_name": "customer_aadhaar",
    "is_pii": true,
    "pii_type": "aadhaar",
    "confidence": 0.95,
    "recommended_technique": "masking",
    "reasoning": "Column name and format indicate Aadhaar number"
  }}
]
"""
        
        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
                
            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2048
                )
                response_text = response.choices[0].message.content
            
            elif self.provider == "github":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2048
                )
                response_text = response.choices[0].message.content
            
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
