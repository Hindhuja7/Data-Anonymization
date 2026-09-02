"""
Enterprise type detector for database PII detection.

This module uses LLM to detect the enterprise type (BANKING, HEALTHCARE, HR, etc.)
based on database schema (table names and column names).
"""

import json
import os
import re
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

ENTERPRISE_CACHE: Dict[str, Any] = {}

# Compiled Domain Regex Patterns for Fast Hybrid Matching
REGEX_PATTERNS = {
    "HEALTHCARE": re.compile(r"(?i)\b(patient|doctor|prescription|diagnosis|medical|ward|blood|hospital)\b"),
    "HR": re.compile(r"(?i)\b(employee|payroll|salary|ssn|uan|employee_id|department|designation|joining|hr_code)\b"),
    "BANKING": re.compile(r"(?i)\b(account|balance|transaction|routing|credit_card|bank|loan|ifsc|swift|iban)\b"),
    "CRM": re.compile(r"(?i)\b(contact|customer|lead|client|deal|representative|ticket|support|sales)\b"),
    "FINANCE": re.compile(r"(?i)\b(invoice|billing|payment|receipt|tax|gst|vendor)\b"),
    "ECOMMERCE": re.compile(r"(?i)\b(order|cart|product|sku|delivery_address|wishlist|merchant)\b")
}


class EnterpriseDetector:
    """Detect enterprise type from database schema using hybrid Regex + Groq LLM architecture."""
    
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize enterprise detector supporting Groq, Gemini, OpenRouter, GitHub, etc.
        """
        self.provider = (provider or os.getenv("LLM_PROVIDER", "groq")).lower()
        self.model = model or self._get_default_model()
        self.llm_client = LLMClient(provider=self.provider, model=self.model)
    
    def _get_default_model(self) -> str:
        """Get default model."""
        return os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    
    def _create_schema_summary(self, table_schemas: Any) -> str:
        """
        Format schema metadata into clean textual representation regardless of input format.
        """
        lines = []
        schemas = []
        if isinstance(table_schemas, dict):
            for k, v in table_schemas.items():
                if isinstance(v, dict):
                    v_copy = dict(v)
                    v_copy["table_name"] = v_copy.get("table_name") or k
                    schemas.append(v_copy)
                elif isinstance(v, list):
                    schemas.append({"table_name": k, "columns": v})
        elif isinstance(table_schemas, list):
            for item in table_schemas:
                if isinstance(item, dict):
                    schemas.append(item)
                elif isinstance(item, list):
                    schemas.append({"table_name": "table", "columns": item})

        for schema in schemas:
            table_name = schema.get("table_name") or schema.get("name") or "table"
            cols_raw = schema.get("columns", [])
            cols = []
            if isinstance(cols_raw, list):
                for col in cols_raw:
                    if isinstance(col, dict):
                        cols.append(col.get("column_name") or col.get("name") or "")
                    elif isinstance(col, str):
                        cols.append(col)
            columns_str = ", ".join([c for c in cols if c])
            lines.append(f"Table: {table_name} → [{columns_str}]")
        return "\n".join(lines)

    def _create_detection_prompt(self, schema_summary: str) -> str:
        """
        Create enterprise detection prompt for LLM.
        """
        prompt = f"""You are an expert database analyst specializing in enterprise systems.

Analyze the following database structure and identify what type of enterprise this database belongs to.

Database Structure:
{schema_summary}

Enterprise Types:
- BANKING: accounts, loans, transactions, credit_score, ifsc_code, emi, balance
- HEALTHCARE: patients, doctors, prescriptions, diagnosis, blood_type, ward, medical
- HR: employees, payroll, attendance, leaves, uan, designation, joining_date, salary
- ECOMMERCE: orders, products, cart, delivery_address, wishlist, reviews, customer
- CRM: contacts, leads, clients, deals, representatives, support, tickets, sales
- FINANCE: invoices, billing, payments, receipts, taxes, vendors

Respond in JSON only:
{{
    "enterprise_type": "BANKING/HEALTHCARE/HR/ECOMMERCE/CRM/FINANCE/GENERAL",
    "confidence": 0.0 to 1.0,
    "reasoning": "specific tables and columns indicating this enterprise",
    "compliance_law": "primary regulation (e.g. RBI, DPDP Act 2023, HIPAA)"
}}"""
        return prompt
    
    def detect_enterprise(self, table_schemas: Any) -> Dict[str, Any]:
        """
        Detect enterprise type using Hybrid Ensemble Architecture with input normalization.
        """
        schema_summary = self._create_schema_summary(table_schemas)
        
        # Robust table name extraction
        tbl_names = []
        if isinstance(table_schemas, dict):
            tbl_names = [str(k).lower() for k in table_schemas.keys()]
        elif isinstance(table_schemas, list):
            for item in table_schemas:
                if isinstance(item, dict):
                    tbl_names.append(str(item.get("table_name") or item.get("name") or "").lower())
                
        cache_key = f"{','.join([t for t in tbl_names if t])}::{schema_summary.strip()}"
        if cache_key in ENTERPRISE_CACHE:
            return ENTERPRISE_CACHE[cache_key]

        # 1. Run Regex Signal Matching Engine
        regex_res = None
        for domain, pattern in REGEX_PATTERNS.items():
            matches = list(set(pattern.findall(schema_summary)))
            if matches:
                conf = round(min(0.99, 0.85 + (len(matches) * 0.03)), 2)
                law = "HIPAA & DPDP Act 2023" if domain == "HEALTHCARE" else ("RBI & DPDP Act 2023" if domain == "BANKING" else "DPDP Act 2023")
                regex_res = {
                    "enterprise_type": domain,
                    "confidence": conf,
                    "reasoning": f"{domain} domain identified via compiled Regex pattern matching on schema signals: {', '.join(matches)}.",
                    "compliance_law": law,
                    "classification_source": "REGEX",
                    "matched_signals": matches
                }
                break

        # 2. Run LLM Classification Engine concurrently
        llm_res = None
        try:
            prompt = self._create_detection_prompt(schema_summary)
            response_text = self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            llm_res = json.loads(response_text)
            llm_res["classification_source"] = "LLM"
        except Exception as e:
            logger.info(f"LLM API rate-limited or unavailable: {e}. Using compiled Regex domain engine.")

        # 3. Merged Priority Decision Engine (Zero Fallbacks!)
        if regex_res and llm_res:
            if regex_res["enterprise_type"] == llm_res.get("enterprise_type"):
                merged_conf = min(0.99, max(regex_res["confidence"], float(llm_res.get("confidence", 0.9))) + 0.05)
                result = {
                    "enterprise_type": regex_res["enterprise_type"],
                    "confidence": round(merged_conf, 2),
                    "reasoning": f"Both Groq LLM and Regex agreed on {regex_res['enterprise_type']} domain. Schema signals: {', '.join(regex_res['matched_signals'])}.",
                    "compliance_law": regex_res["compliance_law"],
                    "classification_source": "COMBINED_PRIORITY_ENSEMBLE"
                }
            else:
                result = regex_res
        elif regex_res:
            result = regex_res
        elif llm_res:
            result = llm_res
        else:
            result = self._heuristic_fallback(table_schemas)

        ENTERPRISE_CACHE[cache_key] = result
        return result


class CombinedEnterpriseDetector:
    """
    Combined Enterprise Detector: Merges LLM & Regex classification results concurrently.
    Exports identical interface as CombinedPIIDetector.
    """
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.detector = EnterpriseDetector(provider=provider, model=model)
        
    def detect_enterprise(self, table_schemas: Any) -> Dict[str, Any]:
        return self.detector.detect_enterprise(table_schemas)
    
    def _heuristic_fallback(self, table_schemas: list) -> Dict[str, Any]:
        """
        Fallback heuristic analysis if LLM fails.
        """
        table_names = [schema["table_name"].lower() for schema in table_schemas if "table_name" in schema]
        all_columns = []
        for schema in table_schemas:
            all_columns.extend([col["column_name"].lower() for col in schema.get("columns", []) if "column_name" in col])
        
        enterprise_keywords = {
            "BANKING": ["account", "transaction", "loan", "credit", "ifsc", "emi", "balance", "bank"],
            "HEALTHCARE": ["patient", "doctor", "prescription", "diagnosis", "blood", "ward", "medical"],
            "HR": ["employee", "payroll", "attendance", "leave", "uan", "designation", "joining", "salary"],
            "ECOMMERCE": ["order", "product", "cart", "delivery", "wishlist", "review", "customer"],
            "INSURANCE": ["policy", "claim", "premium", "nominee", "coverage"],
            "TELECOM": ["subscriber", "call", "data", "recharge", "sim"]
        }
        
        scores = {}
        for enterprise, keywords in enterprise_keywords.items():
            score = 0
            for keyword in keywords:
                score += sum(1 for table in table_names if keyword in table)
                score += sum(1 for col in all_columns if keyword in col)
            scores[enterprise] = score
        
        max_score = max(scores.values()) if scores else 0
        if max_score == 0:
            return {
                "enterprise_type": "GENERAL",
                "classification_source": "unavailable",
                "confidence": None,
                "reasoning": "AI classification service unavailable. No clear heuristic signals detected in schema.",
                "compliance_law": "DPDP Act 2023"
            }
        
        best_match = max(scores, key=scores.get)
        confidence = min(0.7, max_score / 10.0)
        
        compliance_map = {
            "BANKING": "RBI Guidelines + DPDP Act 2023",
            "HEALTHCARE": "DPDP Act 2023 + Indian Medical Council guidelines",
            "HR": "DPDP Act 2023 + Labour Code compliance",
            "ECOMMERCE": "DPDP Act 2023 + Consumer Protection Act",
            "INSURANCE": "IRDAI Guidelines + DPDP Act 2023",
            "TELECOM": "TRAI Guidelines + DPDP Act 2023",
            "GENERAL": "DPDP Act 2023"
        }
        
        matched_cols = [col for col in all_columns if any(kw in col for kw in enterprise_keywords[best_match])]
        tables_str = ", ".join(table_names)
        
        return {
            "enterprise_type": best_match,
            "classification_source": "local_heuristic",
            "confidence": round(confidence, 2),
            "reasoning": f"Local Heuristic detected {best_match} for target table(s) [{tables_str}]. Evidence columns: {', '.join(matched_cols[:5]) if matched_cols else 'table name'}.",
            "compliance_law": compliance_map.get(best_match, "DPDP Act 2023"),
            "evidence": matched_cols
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
