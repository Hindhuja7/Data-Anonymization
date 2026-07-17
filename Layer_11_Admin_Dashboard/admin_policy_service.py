"""
Admin Policy Review and Approval Service

Provides backend functionality for:
- Retrieving DRAFT policies for review
- Overriding column anonymization techniques
- Approving/rejecting policies with audit trail
- Preventing execution of non-APPROVED policies

This service is designed to be called by future frontend admin dashboard
or CLI tools. It wraps PolicyGenerator methods with a clean API.
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# Path bootstrapper to allow flat imports across layers
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _layer in ["Layer_01_Connection_Extraction", "Layer_02_Enterprise_Classification", "Layer_03_PII_Detection", "Layer_04_Change_Detection", "Layer_05_Redis_Hash_Vault", "Layer_06_Redis_AOF_Safety", "Layer_07_Polling_Worker", "Layer_08_Destination_Loader", "Layer_09_Validation_Engine", "Layer_10_Audit_Report", "Layer_11_Admin_Dashboard", "Layer_12_Approval_Workflow"]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from policy_generator import PolicyGenerator


class AdminPolicyService:
    """
    Service for admin policy review and approval workflow.
    """
    
    def __init__(self, policy_file: str = "anonymization_policy.json"):
        """
        Initialize admin policy service.
        
        Args:
            policy_file: Path to the policy JSON file
        """
        self.policy_file = policy_file
        self.policy_generator = PolicyGenerator()
        self.policy_generator.policy_file = policy_file
    
    def get_policy_for_review(self) -> Dict[str, Any]:
        """
        Retrieve the current policy for admin review.
        
        Returns:
            Complete policy dictionary
            
        Raises:
            FileNotFoundError: If policy file does not exist
            ValueError: If policy is invalid
        """
        try:
            policy = self.policy_generator.load_policy(self.policy_file)
            
            # Add review metadata
            policy["review_metadata"] = {
                "policy_file": self.policy_file,
                "current_status": policy["policy_metadata"]["status"],
                "is_approvable": policy["policy_metadata"]["status"] == "DRAFT",
                "total_columns": len(policy["column_policies"]),
                "pii_columns": sum(1 for col in policy["column_policies"] if col["is_pii"]),
                "admin_overrides": sum(1 for col in policy["column_policies"] if col.get("admin_override", False))
            }
            
            return policy
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Policy file not found: {self.policy_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in policy file: {e}")
    
    def get_policy_status(self) -> Dict[str, Any]:
        """
        Get the current status of the policy.
        
        Returns:
            Dictionary with status information
        """
        policy = self.policy_generator.load_policy(self.policy_file)
        
        return {
            "status": policy["policy_metadata"]["status"],
            "policy_version": policy["policy_metadata"]["policy_version"],
            "generated_at": policy["policy_metadata"]["generated_at"],
            "approved_by": policy["policy_metadata"].get("approved_by"),
            "approved_at": policy["policy_metadata"].get("approved_at"),
            "comments": policy["policy_metadata"].get("comments", []),
            "is_approved": policy["policy_metadata"]["status"] == "APPROVED",
            "is_rejected": policy["policy_metadata"]["status"] == "REJECTED",
            "is_draft": policy["policy_metadata"]["status"] == "DRAFT"
        }
    
    def override_column_technique(
        self,
        table_name: str,
        column_name: str,
        new_technique: str,
        admin_name: str,
        admin_comment: str = ""
    ) -> bool:
        """
        Override the anonymization technique for a specific column.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            new_technique: New anonymization technique (NO_CHANGE, TOKENIZATION, MASKING, HASHING, DIFFERENTIAL_PRIVACY, REDACTION)
            admin_name: Name of the admin making the override
            admin_comment: Comment explaining the override
            
        Returns:
            True if override successful, False if column not found
            
        Raises:
            ValueError: If policy is not in DRAFT status
        """
        # Check if policy is in DRAFT status
        status = self.get_policy_status()["status"]
        if status != "DRAFT":
            raise ValueError(f"Cannot override column technique when policy status is '{status}'. Only DRAFT policies can be modified.")
        
        # Load policy
        policy = self.policy_generator.load_policy(self.policy_file)
        
        # Find the column and get current technique
        current_technique = None
        for col_policy in policy["column_policies"]:
            if col_policy["table_name"] == table_name and col_policy["column_name"] == column_name:
                current_technique = col_policy["anonymization_technique"]
                break
        
        if current_technique is None:
            return False
        
        # Apply override using PolicyGenerator method
        success = self.policy_generator.override_column_policy(
            table_name=table_name,
            column_name=column_name,
            new_technique=new_technique,
            admin_comments=admin_comment
        )
        
        if success:
            # Add audit comment
            timestamp = datetime.now().isoformat()
            audit_comment = f"[{timestamp}] {admin_name} overridden technique from {current_technique} to {new_technique}"
            if admin_comment:
                audit_comment += f": {admin_comment}"
            
            self.policy_generator.update_policy_status(
                status="DRAFT",  # Keep as DRAFT
                approved_by=admin_name,
                comments=[audit_comment]
            )
            
            # Save updated policy
            self.policy_generator.save_policy(self.policy_file)
        
        return success
    
    def approve_policy(
        self,
        admin_name: str,
        comments: Optional[List[str]] = None
    ) -> bool:
        """
        Approve the policy for execution.
        
        Args:
            admin_name: Name of the admin approving the policy
            comments: Optional list of approval comments
            
        Returns:
            True if approval successful
            
        Raises:
            ValueError: If policy is not in DRAFT status
        """
        # Check if policy is in DRAFT status
        status = self.get_policy_status()["status"]
        if status != "DRAFT":
            raise ValueError(f"Cannot approve policy when status is '{status}'. Only DRAFT policies can be approved.")
        
        # Add approval timestamp comment
        timestamp = datetime.now().isoformat()
        approval_comment = f"[{timestamp}] Policy approved by {admin_name}"
        
        if comments:
            all_comments = [approval_comment] + comments
        else:
            all_comments = [approval_comment]
        
        # Update status to APPROVED
        self.policy_generator.update_policy_status(
            status="APPROVED",
            approved_by=admin_name,
            comments=all_comments
        )
        
        # Save updated policy
        self.policy_generator.save_policy(self.policy_file)
        
        return True
    
    def reject_policy(
        self,
        admin_name: str,
        comments: Optional[List[str]] = None
    ) -> bool:
        """
        Reject the policy.
        
        Args:
            admin_name: Name of the admin rejecting the policy
            comments: Optional list of rejection comments (required for rejection)
            
        Returns:
            True if rejection successful
            
        Raises:
            ValueError: If policy is not in DRAFT status or no comments provided
        """
        # Check if policy is in DRAFT status
        status = self.get_policy_status()["status"]
        if status != "DRAFT":
            raise ValueError(f"Cannot reject policy when status is '{status}'. Only DRAFT policies can be rejected.")
        
        # Comments are required for rejection
        if not comments:
            raise ValueError("Comments are required when rejecting a policy to explain the rejection reason.")
        
        # Add rejection timestamp comment
        timestamp = datetime.now().isoformat()
        rejection_comment = f"[{timestamp}] Policy rejected by {admin_name}"
        
        all_comments = [rejection_comment] + comments
        
        # Update status to REJECTED
        self.policy_generator.update_policy_status(
            status="REJECTED",
            approved_by=admin_name,
            comments=all_comments
        )
        
        # Save updated policy
        self.policy_generator.save_policy(self.policy_file)
        
        return True
    
    def reset_to_draft(self, admin_name: str, reason: str) -> bool:
        """
        Reset an APPROVED or REJECTED policy back to DRAFT status.
        This is useful if the policy needs to be re-reviewed after changes.
        
        Args:
            admin_name: Name of the admin resetting the policy
            reason: Reason for resetting to DRAFT
            
        Returns:
            True if reset successful
            
        Raises:
            ValueError: If policy is already in DRAFT status
        """
        # Check if policy is not in DRAFT status
        status = self.get_policy_status()["status"]
        if status == "DRAFT":
            raise ValueError("Policy is already in DRAFT status.")
        
        # Add reset comment
        timestamp = datetime.now().isoformat()
        reset_comment = f"[{timestamp}] Policy reset to DRAFT by {admin_name}: {reason}"
        
        # Clear approved_by and approved_at
        policy = self.policy_generator.load_policy(self.policy_file)
        policy["policy_metadata"]["approved_by"] = None
        policy["policy_metadata"]["approved_at"] = None
        
        # Update status to DRAFT
        self.policy_generator.update_policy_status(
            status="DRAFT",
            approved_by=None,
            comments=[reset_comment]
        )
        
        # Save updated policy
        self.policy_generator.save_policy(self.policy_file)
        
        return True
    
    def get_column_policy(self, table_name: str, column_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the policy for a specific column.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            
        Returns:
            Column policy dictionary or None if not found
        """
        policy = self.policy_generator.load_policy(self.policy_file)
        
        for col_policy in policy["column_policies"]:
            if col_policy["table_name"] == table_name and col_policy["column_name"] == column_name:
                return col_policy
        
        return None
    
    def get_pii_columns_summary(self) -> List[Dict[str, Any]]:
        """
        Get a summary of all PII columns for review.
        
        Returns:
            List of PII column policies sorted by table and column name
        """
        policy = self.policy_generator.load_policy(self.policy_file)
        
        pii_columns = [
            col for col in policy["column_policies"]
            if col["is_pii"]
        ]
        
        # Sort by table name, then column name
        pii_columns.sort(key=lambda x: (x["table_name"], x["column_name"]))
        
        return pii_columns
