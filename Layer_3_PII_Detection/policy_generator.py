"""
Anonymization Policy Generator

Converts PII detection results into a formal, reviewable anonymization policy.
This policy can be reviewed and modified by administrators before execution.
"""

import json
import os
import sys
from typing import Dict, List, Any
from datetime import datetime

# Path bootstrapper to allow flat imports across layers
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _layer in ["Layer_1_Connection_Extraction", "Layer_2_Enterprise_Classification", "Layer_3_PII_Detection", "Layer_4_Anonymization_Vault"]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)


class PolicyGenerator:
    """
    Generates column-level anonymization policies from PII detection results.
    """
    
    def __init__(self):
        """Initialize the policy generator."""
        self.policy = {
            "policy_metadata": {
                "policy_version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "status": "DRAFT",  # DRAFT, APPROVED, REJECTED
                "approved_by": None,
                "approved_at": None,
                "comments": []
            },
            "database_info": {},
            "enterprise_info": {},
            "column_policies": []
        }
    
    def generate_policy(
        self,
        pii_report: Dict[str, Any],
        schema_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate a column-level anonymization policy from PII detection results.
        
        Args:
            pii_report: PII detection report from database_pii_detection
            schema_info: Optional schema information for additional context
        
        Returns:
            Dictionary containing the complete anonymization policy
        """
        # Extract database and enterprise information
        self.policy["database_info"] = {
            "database_name": pii_report.get("database_name"),
            "database_type": pii_report.get("database_type")
        }
        
        self.policy["enterprise_info"] = {
            "enterprise_type": pii_report.get("enterprise_type"),
            "enterprise_confidence": pii_report.get("enterprise_confidence"),
            "compliance_law": pii_report.get("compliance_law")
        }
        
        # Generate column-level policies
        column_policies = []
        
        for table in pii_report.get("tables", []):
            table_name = table["table_name"]
            
            # Get schema information for this table if available
            table_schema = schema_info.get(table_name, {}) if schema_info else {}
            primary_keys = table_schema.get("primary_keys", [])
            foreign_keys = table_schema.get("foreign_keys", [])
            
            for column_info in table.get("columns", []):
                column_name = column_info["column_name"]
                is_pii = column_info.get("is_pii", False)
                pii_type = column_info.get("pii_type")
                confidence = column_info.get("confidence", 0.0)
                recommended_technique = column_info.get("recommended_technique", "NO_CHANGE")
                
                # Determine if column is primary key or foreign key
                is_primary_key = column_name in primary_keys
                is_foreign_key = False
                foreign_key_details = None
                
                for fk in foreign_keys:
                    if column_name in fk.get("constrained_columns", []):
                        is_foreign_key = True
                        foreign_key_details = {
                            "referred_table": fk.get("referred_table"),
                            "referred_columns": fk.get("referred_columns")
                        }
                        break
                
                # Generate policy entry for this column
                column_policy = {
                    "table_name": table_name,
                    "column_name": column_name,
                    "is_pii": is_pii,
                    "pii_type": pii_type if is_pii else None,
                    "confidence": confidence,
                    "anonymization_technique": recommended_technique if is_pii else "NO_CHANGE",
                    "reason": self._generate_reason(column_info, is_pii, pii_type, recommended_technique),
                    "is_primary_key": is_primary_key,
                    "is_foreign_key": is_foreign_key,
                    "foreign_key_details": foreign_key_details,
                    "data_type": self._get_data_type(table_schema, column_name),
                    "admin_override": False,  # Can be set by admin during review
                    "admin_comments": ""  # Can be filled by admin during review
                }
                
                column_policies.append(column_policy)
        
        self.policy["column_policies"] = column_policies
        
        # Generate summary statistics
        self.policy["policy_summary"] = self._generate_summary(column_policies)
        
        return self.policy
    
    def _generate_reason(
        self,
        column_info: Dict[str, Any],
        is_pii: bool,
        pii_type: str,
        technique: str
    ) -> str:
        """
        Generate a human-readable reason for the policy decision.
        
        Args:
            column_info: Column information from PII detection
            is_pii: Whether column is identified as PII
            pii_type: Type of PII if applicable
            technique: Recommended anonymization technique
        
        Returns:
            Human-readable reason string
        """
        if not is_pii:
            return "Column identified as non-PII. No anonymization required."
        
        reason_parts = []
        
        # Add PII type information
        if pii_type:
            reason_parts.append(f"Column identified as {pii_type}")
        
        # Add technique justification
        technique_justifications = {
            "TOKENIZATION": "Replace with realistic fake values for usability while protecting privacy",
            "MASKING": "Mask sensitive characters to preserve format while obscuring data",
            "HASHING": "One-way hash for irreversible identification protection",
            "DIFFERENTIAL_PRIVACY": "Add statistical noise to preserve statistical properties",
            "PSEUDONYMIZATION": "Replace with consistent pseudonyms for referential integrity",
            "GENERALIZATION": "Generalize to broader categories for privacy protection",
            "REDACTION": "Complete removal for highly sensitive data",
            "NO_CHANGE": "No anonymization required"
        }
        
        if technique in technique_justifications:
            reason_parts.append(technique_justifications[technique])
        
        # Add confidence information
        confidence = column_info.get("confidence", 0.0)
        if confidence >= 0.9:
            reason_parts.append("High confidence detection")
        elif confidence >= 0.7:
            reason_parts.append("Medium confidence detection")
        elif confidence < 0.7:
            reason_parts.append("Lower confidence detection - manual review recommended")
        
        return ". ".join(reason_parts) + "."
    
    def _get_data_type(self, table_schema: Dict[str, Any], column_name: str) -> str:
        """
        Get data type for a column from schema information.
        
        Args:
            table_schema: Table schema information
            column_name: Name of the column
        
        Returns:
            Data type string or "UNKNOWN" if not found
        """
        for col_info in table_schema.get("columns", []):
            if col_info.get("column_name") == column_name:
                return col_info.get("data_type", "UNKNOWN")
        return "UNKNOWN"
    
    def _generate_summary(self, column_policies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics for the policy.
        
        Args:
            column_policies: List of column policy entries
        
        Returns:
            Dictionary containing summary statistics
        """
        total_columns = len(column_policies)
        pii_columns = [c for c in column_policies if c["is_pii"]]
        non_pii_columns = [c for c in column_policies if not c["is_pii"]]
        
        # Count by technique
        technique_counts = {}
        for policy in column_policies:
            technique = policy["anonymization_technique"]
            technique_counts[technique] = technique_counts.get(technique, 0) + 1
        
        # Count by PII type
        pii_type_counts = {}
        for policy in pii_columns:
            pii_type = policy["pii_type"]
            if pii_type:
                pii_type_counts[pii_type] = pii_type_counts.get(pii_type, 0) + 1
        
        # Count by table
        table_counts = {}
        for policy in column_policies:
            table_name = policy["table_name"]
            table_counts[table_name] = table_counts.get(table_name, 0) + 1
        
        return {
            "total_columns": total_columns,
            "pii_columns": len(pii_columns),
            "non_pii_columns": len(non_pii_columns),
            "pii_percentage": round((len(pii_columns) / total_columns * 100), 1) if total_columns > 0 else 0,
            "technique_distribution": technique_counts,
            "pii_type_distribution": pii_type_counts,
            "table_distribution": table_counts
        }
    
    def save_policy(self, filepath: str = "anonymization_policy.json") -> str:
        """
        Save the generated policy to a JSON file.
        
        Args:
            filepath: Path to save the policy file
        
        Returns:
            Path where the policy was saved
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.policy, f, indent=2, ensure_ascii=False)
        return filepath
    
    def load_policy(self, filepath: str) -> Dict[str, Any]:
        """
        Load a policy from a JSON file.
        
        Args:
            filepath: Path to the policy file
        
        Returns:
            Loaded policy dictionary
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            self.policy = json.load(f)
        return self.policy
    
    def update_policy_status(
        self,
        status: str,
        approved_by: str = None,
        comments: List[str] = None
    ):
        """
        Update the policy status (for admin review workflow).
        
        Args:
            status: New status (DRAFT, APPROVED, REJECTED)
            approved_by: Name of person approving/rejecting
            comments: Optional comments about the decision
        """
        self.policy["policy_metadata"]["status"] = status
        if status in ["APPROVED", "REJECTED"]:
            self.policy["policy_metadata"]["approved_by"] = approved_by
            self.policy["policy_metadata"]["approved_at"] = datetime.now().isoformat()
        
        if comments:
            self.policy["policy_metadata"]["comments"].extend(comments)
    
    def override_column_policy(
        self,
        table_name: str,
        column_name: str,
        new_technique: str,
        admin_comments: str = ""
    ):
        """
        Allow admin to override a specific column's anonymization technique.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            new_technique: New anonymization technique to apply
            admin_comments: Comments explaining the override
        """
        for policy in self.policy["column_policies"]:
            if policy["table_name"] == table_name and policy["column_name"] == column_name:
                policy["anonymization_technique"] = new_technique
                policy["admin_override"] = True
                policy["admin_comments"] = admin_comments
                return True
        
        return False


def generate_policy_from_detection(
    pii_report: Dict[str, Any],
    schema_info: Dict[str, Any] = None,
    output_file: str = "anonymization_policy.json"
) -> Dict[str, Any]:
    """
    Convenience function to generate policy from PII detection results.
    
    Args:
        pii_report: PII detection report from database_pii_detection
        schema_info: Optional schema information
        output_file: Path to save the policy file
    
    Returns:
        Generated policy dictionary
    """
    generator = PolicyGenerator()
    policy = generator.generate_policy(pii_report, schema_info)
    generator.save_policy(output_file)
    return policy


if __name__ == "__main__":
    # Example usage
    sample_pii_report = {
        "database_name": "testdb",
        "database_type": "postgresql",
        "enterprise_type": "BANKING",
        "enterprise_confidence": 0.9,
        "compliance_law": "RBI Guidelines, DPDP Act 2023",
        "tables": [
            {
                "table_name": "customers",
                "columns": [
                    {
                        "column_name": "customer_id",
                        "is_pii": True,
                        "pii_type": "IDENTIFIER",
                        "confidence": 1.0,
                        "recommended_technique": "HASHING"
                    },
                    {
                        "column_name": "full_name",
                        "is_pii": True,
                        "pii_type": "FULL_NAME",
                        "confidence": 0.95,
                        "recommended_technique": "TOKENIZATION"
                    },
                    {
                        "column_name": "created_at",
                        "is_pii": False,
                        "pii_type": None,
                        "confidence": 0.0,
                        "recommended_technique": None
                    }
                ]
            }
        ]
    }
    
    # Generate policy
    policy = generate_policy_from_detection(sample_pii_report)
    print("Policy generated successfully!")
    print(f"Total columns: {policy['policy_summary']['total_columns']}")
    print(f"PII columns: {policy['policy_summary']['pii_columns']}")
    print(f"Non-PII columns: {policy['policy_summary']['non_pii_columns']}")
