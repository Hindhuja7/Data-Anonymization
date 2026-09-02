"""
Approval workflow validation gating.
Protects the pipeline by blocking execution unless the anonymization policy status is approved.
"""

import logging

logger = logging.getLogger(__name__)

class ApprovalWorkflow:
    """Handles human-in-the-loop review approval checks protecting sandbox insertion."""
    
    @staticmethod
    def is_policy_approved(policy: dict) -> bool:
        """
        Validate that the policy has been approved by an administrator.
        
        Returns:
            True if policy metadata status is 'APPROVED', False otherwise.
        """
        metadata = policy.get("policy_metadata", {})
        status = metadata.get("status")
        version = metadata.get("policy_version", "1.0")
        approved_by = metadata.get("approved_by")
        
        if status == "APPROVED":
            print(f"[OK] Policy loaded and approved (version {version}) by {approved_by or 'Admin'}")
            return True
            
        print(f"ERROR: Only APPROVED policies can be executed. Current status: {status}")
        return False
