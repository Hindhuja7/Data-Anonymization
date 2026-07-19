"""
Enterprise type detector for database PII detection.

This module uses LLM to detect the enterprise type (BANKING, HEALTHCARE, HR, etc.)
based on database schema (table names and column names).
"""

import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import logging

import sys
import os
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _layer in ["Connection_Extraction", "Enterprise_Classification", "PII_Detection", "Change_Detection", "Redis_Hash_Vault", "Redis_AOF_Safety", "Polling_Worker", "Destination_Loader", "Validation_Engine", "Audit_Report", "Admin_Dashboard", "Approval_Workflow"]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from llm_client import LLMClient

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnterpriseDetector:
    """Detect enterprise type from database schema using LLM."""
    
    def __init__(self, provider: str = "github", model: str = None):
        """
        Initialize enterprise detector.
        
        Args:
            provider: Must be 'github' (only GitHub models supported)
            model: Model name (default depends on provider)
        """
        if provider != "github":
            raise ValueError("Only GitHub models are supported. Provider must be 'github'.")
        
        self.provider = provider
        self.model = model or self._get_default_model()
        self.llm_client = LLMClient(provider=provider, model=model)
    
    def _get_default_model(self) -> str:
        """Get default model."""
        return os.getenv("LLM_MODEL", "gpt-4o")
    
    def _create_schema_summary(self, table_schemas: list) -> str:
        """
        Create schema summary string for LLM prompt.
        
        Args:
            table_schemas: List of table schema dictionaries
        
        Returns:
            Formatted schema summary string
        """
        lines = []
        for schema in table_schemas:
            table_name = schema["table_name"]
            columns = [col["column_name"] for col in schema["columns"]]
            columns_str = ", ".join(columns)
            lines.append(f"Table: {table_name} → [{columns_str}]")
        return "\n".join(lines)
    
    def _create_detection_prompt(self, schema_summary: str) -> str:
        """
        Create enterprise detection prompt for LLM.
        
        Args:
            schema_summary: Formatted schema summary
        
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert database analyst specializing in Indian enterprise systems.

Analyze the following database structure and identify what type of enterprise this database belongs to.

Database Structure:
{schema_summary}

Enterprise Types:
- BANKING: accounts, loans, transactions, credit_score, ifsc_code, emi
- HEALTHCARE: patients, doctors, prescriptions, diagnosis, blood_type, ward
- HR: employees, payroll, attendance, leaves, uan, designation, joining_date
- ECOMMERCE: orders, products, cart, delivery_address, wishlist, reviews
- INSURANCE: policies, claims, premiums, nominees, coverage
- TELECOM: subscribers, calls, data_usage, recharge, sim_details
- GENERAL: cannot determine clearly from available information

Thinking steps before answering:
1. Which table names suggest a specific industry?
2. Which column names are industry-specific?
3. Are there regulatory identifiers (UAN=HR, IFSC=banking, diagnosis=healthcare)?
4. What combination of tables makes most sense together?
5. How confident am I based on the signals available?

Important rules:
- If multiple enterprise types are present, pick the PRIMARY one
- If signals are weak or generic, use GENERAL with low confidence
- confidence below 0.5 means fall back to GENERAL treatment

Respond in JSON only, no extra text:
{{
    "enterprise_type": "BANKING/HEALTHCARE/HR/ECOMMERCE/INSURANCE/TELECOM/GENERAL",
    "confidence": 0.0 to 1.0,
    "reasoning": "which specific tables and columns indicate this enterprise",
    "compliance_law": "primary regulation that applies (e.g. RBI Guidelines, DPDP Act 2023, HIPAA equivalent)"
}}"""
        return prompt
    
    def detect_enterprise(self, table_schemas: list) -> Dict[str, Any]:
        """
        Detect enterprise type from database schema.
        
        Args:
            table_schemas: List of table schema dictionaries
        
        Returns:
            Dictionary with enterprise_type, confidence, reasoning, compliance_law
        """
        schema_summary = self._create_schema_summary(table_schemas)
        prompt = self._create_detection_prompt(schema_summary)
        
        try:
            # Use LLMClient with automatic fallback
            response_text = self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024
            )
            
            # Log which model was used
            provider, model = self.llm_client.get_current_model()
            logger.info(f"Enterprise detection used: {provider}/{model}")
            
            # Clean and parse JSON response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["enterprise_type", "confidence", "reasoning", "compliance_law"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            logger.info(f"Enterprise detected: {result['enterprise_type']} (confidence: {result['confidence']})")
            return result
            
        except Exception as e:
            logger.error(f"Enterprise detection failed: {e}. Using heuristic fallback.")
            return self._heuristic_fallback(table_schemas)
    
    def _heuristic_fallback(self, table_schemas: list) -> Dict[str, Any]:
        """
        Fallback heuristic analysis if LLM fails.
        
        Args:
            table_schemas: List of table schema dictionaries
        
        Returns:
            Dictionary with enterprise_type, confidence, reasoning, compliance_law
        """
        # Collect all table and column names
        table_names = [schema["table_name"].lower() for schema in table_schemas]
        all_columns = []
        for schema in table_schemas:
            all_columns.extend([col["column_name"].lower() for col in schema["columns"]])
        
        # Keyword matching
        enterprise_keywords = {
            "BANKING": ["account", "transaction", "loan", "credit", "ifsc", "emi", "balance", "bank"],
            "HEALTHCARE": ["patient", "doctor", "prescription", "diagnosis", "blood", "ward", "medical"],
            "HR": ["employee", "payroll", "attendance", "leave", "uan", "designation", "joining", "salary"],
            "ECOMMERCE": ["order", "product", "cart", "delivery", "wishlist", "review", "customer"],
            "INSURANCE": ["policy", "claim", "premium", "nominee", "coverage"],
            "TELECOM": ["subscriber", "call", "data", "recharge", "sim"]
        }
        
        # Score each enterprise type
        scores = {}
        for enterprise, keywords in enterprise_keywords.items():
            score = 0
            for keyword in keywords:
                score += sum(1 for table in table_names if keyword in table)
                score += sum(1 for col in all_columns if keyword in col)
            scores[enterprise] = score
        
        # Find highest score
        max_score = max(scores.values())
        if max_score == 0:
            return {
                "enterprise_type": "GENERAL",
                "confidence": 0.3,
                "reasoning": "No clear enterprise signals detected in table/column names",
                "compliance_law": "DPDP Act 2023"
            }
        
        best_match = max(scores, key=scores.get)
        confidence = min(0.7, max_score / 10.0)  # Cap at 0.7 for heuristic
        
        # Map to compliance law
        compliance_map = {
            "BANKING": "RBI Guidelines + DPDP Act 2023",
            "HEALTHCARE": "DPDP Act 2023 + Indian Medical Council guidelines",
            "HR": "DPDP Act 2023 + Labour Code compliance",
            "ECOMMERCE": "DPDP Act 2023 + Consumer Protection Act",
            "INSURANCE": "IRDAI Guidelines + DPDP Act 2023",
            "TELECOM": "TRAI Guidelines + DPDP Act 2023",
            "GENERAL": "DPDP Act 2023"
        }
        
        return {
            "enterprise_type": best_match,
            "confidence": confidence,
            "reasoning": f"Heuristic analysis detected {best_match} based on keyword matching in table/column names",
            "compliance_law": compliance_map.get(best_match, "DPDP Act 2023")
        }


def detect_enterprise_from_schema(
    table_schemas: list,
    provider: str = "github",
    model: str = None
) -> Dict[str, Any]:
    """
    Convenience function to detect enterprise type.
    
    Args:
        table_schemas: List of table schema dictionaries
        provider: LLM provider (github, openai, anthropic)
        model: Model name
    
    Returns:
        Dictionary with enterprise_type, confidence, reasoning, compliance_law
    """
    detector = EnterpriseDetector(provider=provider, model=model)
    return detector.detect_enterprise(table_schemas)
