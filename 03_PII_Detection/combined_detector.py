"""
Combined PII Detector - Merges LLM and Regex detection results.
Provides a unified detection interface with intelligent result merging.
"""

import sys
import os
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _layer in ["01_Connection_Extraction", "02_Enterprise_Classification", "03_PII_Detection", "04_Change_Detection", "05_Redis_Hash_Vault", "06_Redis_AOF_Safety", "07_Polling_Worker", "08_Destination_Loader", "09_Validation_Engine", "10_Audit_Report", "11_Admin_Dashboard", "12_Approval_Workflow"]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from typing import Dict, Any, Optional
from llm_pii_detection import detect_pii_with_llm, LLMPiiDetector
from india_regex_patterns import detect_india_pii_column


class CombinedPIIDetector:
    """Combines LLM and regex detection for robust PII identification."""
    
    def __init__(self, provider: str = "github", model: str = None):
        """
        Initialize combined detector.
        
        Args:
            provider: LLM provider ('github', 'openai', 'anthropic')
            model: Specific model name (for GitHub Models)
        """
        self.provider = provider
        self.model = model
    
    def detect_column(
        self,
        column_name: str,
        data_type: str,
        sample_values: list[str],
        table_name: str = None
    ) -> Dict[str, Any]:
        """
        Detect PII in a column using both LLM and regex methods.
        
        Args:
            column_name: Name of the column
            data_type: SQL data type
            sample_values: List of sample values
            table_name: Optional table name
        
        Returns:
            Dictionary with merged detection results
        """
        # Run LLM detection
        llm_result = detect_pii_with_llm(
            column_name=column_name,
            data_type=data_type,
            sample_values=sample_values,
            table_name=table_name,
            provider=self.provider,
            model=self.model
        )
        
        # Run regex detection
        regex_result = detect_india_pii_column(
            column_name=column_name,
            data_type=data_type,
            sample_values=sample_values,
            table_name=table_name
        )
        
        # Merge results
        merged_result = self._merge_results(llm_result, regex_result)
        
        return merged_result
    
    def _merge_results(
        self,
        llm_result: Dict[str, Any],
        regex_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge LLM and regex detection results.
        
        Merging strategy:
        - If both agree: High confidence, use agreed result
        - If LLM says PII, regex doesn't: Trust LLM (context-aware)
        - If regex says PII, LLM doesn't: Medium confidence (might be false positive)
        - If neither says PII: Not PII
        """
        llm_is_pii = llm_result.get("is_pii", False)
        regex_is_pii = regex_result.get("is_pii", False)
        
        # Both agree on PII
        if llm_is_pii and regex_is_pii:
            # Use LLM's PII type (more context-aware)
            # Use higher confidence
            merged_confidence = max(
                llm_result.get("confidence", 0.0),
                regex_result.get("confidence", 0.0)
            )
            
            return {
                "column_name": llm_result.get("column_name"),
                "is_pii": True,
                "pii_type": llm_result.get("pii_type") or regex_result.get("pii_type"),
                "confidence": min(0.99, merged_confidence + 0.05),  # Boost confidence when both agree
                "recommended_technique": llm_result.get("recommended_technique") or regex_result.get("recommended_technique"),
                "reasoning": f"Both LLM and regex detected PII. LLM: {llm_result.get('reasoning')}. Regex: {regex_result.get('reasoning')}",
                "detection_method": "combined",
                "llm_result": llm_result,
                "regex_result": regex_result
            }
        
        # Only LLM detected PII
        elif llm_is_pii and not regex_is_pii:
            return {
                "column_name": llm_result.get("column_name"),
                "is_pii": True,
                "pii_type": llm_result.get("pii_type"),
                "confidence": llm_result.get("confidence", 0.0),
                "recommended_technique": llm_result.get("recommended_technique"),
                "reasoning": f"LLM detected PII (context-aware). Regex did not detect. LLM: {llm_result.get('reasoning')}",
                "detection_method": "llm_primary",
                "llm_result": llm_result,
                "regex_result": regex_result
            }
        
        # Only regex detected PII
        elif not llm_is_pii and regex_is_pii:
            # Lower confidence since LLM (context-aware) didn't detect
            return {
                "column_name": regex_result.get("column_name"),
                "is_pii": True,
                "pii_type": regex_result.get("pii_type"),
                "confidence": max(0.0, regex_result.get("confidence", 0.0) - 0.15),  # Penalize confidence
                "recommended_technique": regex_result.get("recommended_technique"),
                "reasoning": f"Regex detected PII but LLM did not (possible false positive). Regex: {regex_result.get('reasoning')}",
                "detection_method": "regex_primary",
                "llm_result": llm_result,
                "regex_result": regex_result
            }
        
        # Neither detected PII
        else:
            return {
                "column_name": llm_result.get("column_name"),
                "is_pii": False,
                "pii_type": None,
                "confidence": 0.0,
                "recommended_technique": "no_change",
                "reasoning": "Neither LLM nor regex detected PII",
                "detection_method": "combined",
                "llm_result": llm_result,
                "regex_result": regex_result
            }
    
    def detect_multiple_columns(
        self,
        columns: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        Detect PII in multiple columns.
        
        Args:
            columns: List of dicts with keys: column_name, data_type, sample_values, table_name (optional)
        
        Returns:
            List of merged detection results
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
    
    def detect_table(
        self,
        table_name: str,
        columns: list[Dict[str, Any]],
        use_batch: bool = True,
        enterprise_type: str = "GENERAL",
        compliance_law: str = "DPDP Act 2023",
        enterprise_confidence: float = 0.5
    ) -> list[Dict[str, Any]]:
        """
        Detect PII in all columns of a table.
        
        Args:
            table_name: Name of the table
            columns: List of dicts with keys: column_name, data_type, sample_values
            use_batch: If True, use LLM batch detection (single API call). 
                      If False, detect each column individually.
            enterprise_type: Enterprise type (BANKING, HEALTHCARE, HR, etc.)
            compliance_law: Applicable compliance law
            enterprise_confidence: Confidence in enterprise detection (0.0 to 1.0)
        
        Returns:
            List of merged detection results for all columns
        """
        if use_batch:
            # Use LLM batch detection for efficiency
            llm_detector = LLMPiiDetector(provider=self.provider, model=self.model)
            llm_results = llm_detector.detect_table_columns_batch(table_name, columns, enterprise_type, compliance_law, enterprise_confidence)
            
            # Merge each LLM result with regex result
            merged_results = []
            for i, col in enumerate(columns):
                if i < len(llm_results):
                    llm_result = {
                        "column_name": llm_results[i].column_name,
                        "is_pii": llm_results[i].is_pii,
                        "pii_type": llm_results[i].pii_type,
                        "confidence": llm_results[i].confidence,
                        "recommended_technique": llm_results[i].recommended_technique,
                        "reasoning": llm_results[i].reasoning,
                        "model_used": llm_detector.model,
                        "provider_used": llm_detector.provider
                    }
                else:
                    llm_result = {
                        "column_name": col["column_name"],
                        "is_pii": True,
                        "pii_type": "unknown",
                        "confidence": 0.0,
                        "recommended_technique": "tokenization",
                        "reasoning": "Batch processing incomplete - conservative fallback"
                    }
                
                # Get regex result for this column
                regex_result = detect_india_pii_column(
                    column_name=col["column_name"],
                    data_type=col["data_type"],
                    sample_values=col["sample_values"],
                    table_name=table_name
                )
                
                # Merge results
                merged_result = self._merge_results(llm_result, regex_result)
                merged_results.append(merged_result)
            
            return merged_results
        else:
            # Fall back to individual column detection
            return self.detect_multiple_columns(columns)


def detect_pii_combined(
    column_name: str,
    data_type: str,
    sample_values: list[str],
    table_name: str = None,
    provider: str = "github",
    model: str = None
) -> Dict[str, Any]:
    """
    Convenience function for combined PII detection.
    
    Args:
        column_name: Name of the column
        data_type: SQL data type
        sample_values: List of sample values
        table_name: Optional table name
        provider: LLM provider ('github', 'openai', 'anthropic')
        model: Specific model name (for GitHub Models)
    
    Returns:
        Dictionary with merged detection results
    """
    detector = CombinedPIIDetector(provider=provider, model=model)
    return detector.detect_column(column_name, data_type, sample_values, table_name)


if __name__ == "__main__":
    # Test combined detection
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
            "column_name": "product_name",
            "data_type": "VARCHAR(50)",
            "sample_values": ["Laptop", "Mouse", "Keyboard"],
            "table_name": "products"
        }
    ]
    
    print("Combined PII Detection Test")
    print("=" * 70)
    
    for col in test_columns:
        print(f"\nTesting column: {col['column_name']}")
        print(f"Table: {col['table_name']}")
        print(f"Data type: {col['data_type']}")
        print(f"Samples: {col['sample_values'][:3]}")
        print("-" * 70)
        
        try:
            result = detect_pii_combined(
                column_name=col["column_name"],
                data_type=col["data_type"],
                sample_values=col["sample_values"],
                table_name=col["table_name"],
                provider="github"
            )
            
            print(f"Is PII: {result['is_pii']}")
            print(f"PII Type: {result['pii_type']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Recommended Technique: {result['recommended_technique']}")
            print(f"Detection Method: {result['detection_method']}")
            print(f"Reasoning: {result['reasoning']}")
            
        except Exception as e:
            print(f"Error: {e}")
        
        print("=" * 70)
