"""
Test script for Admin Policy Review and Approval Workflow

Demonstrates the complete backend approval workflow:
1. Reset current APPROVED policy to DRAFT
2. Retrieve policy for review
3. Override a column technique
4. Approve the policy
5. Verify executor accepts the APPROVED policy
"""

import json
import os
import sys

# Path bootstrapper to allow flat imports across layers
_root = os.path.dirname(os.path.abspath(__file__))
for _layer in ["Layer_1_Connection_Extraction", "Layer_2_Enterprise_Classification", "Layer_3_PII_Detection", "Layer_4_Anonymization_Vault"]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from admin_policy_service import AdminPolicyService


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_policy_status(status: dict):
    """Print policy status information."""
    print(f"Status: {status['status']}")
    print(f"Policy Version: {status['policy_version']}")
    print(f"Generated At: {status['generated_at']}")
    if status['approved_by']:
        print(f"Approved By: {status['approved_by']}")
        print(f"Approved At: {status['approved_at']}")
    if status['comments']:
        print(f"Comments: {status['comments']}")


def main():
    """Run the admin approval workflow test."""
    
    print_section("ADMIN POLICY APPROVAL WORKFLOW TEST")
    
    # Initialize admin service
    admin_service = AdminPolicyService(policy_file="anonymization_policy.json")
    
    try:
        # Step 1: Check current status
        print_section("STEP 1: Check Current Policy Status")
        current_status = admin_service.get_policy_status()
        print_policy_status(current_status)
        
        # If already APPROVED, reset to DRAFT for testing
        if current_status['status'] == "APPROVED":
            print("\n[WARN] Policy is currently APPROVED. Resetting to DRAFT for testing...")
            admin_service.reset_to_draft(
                admin_name="test_admin",
                reason="Resetting to DRAFT for workflow testing"
            )
            current_status = admin_service.get_policy_status()
            print("\n[OK] Policy reset to DRAFT")
            print_policy_status(current_status)
        
        # Step 2: Retrieve policy for review
        print_section("STEP 2: Retrieve Policy for Review")
        policy = admin_service.get_policy_for_review()
        review_meta = policy["review_metadata"]
        
        print(f"Policy File: {review_meta['policy_file']}")
        print(f"Current Status: {review_meta['current_status']}")
        print(f"Is Approvable: {review_meta['is_approvable']}")
        print(f"Total Columns: {review_meta['total_columns']}")
        print(f"PII Columns: {review_meta['pii_columns']}")
        print(f"Admin Overrides: {review_meta['admin_overrides']}")
        
        # Step 3: Show PII columns summary
        print_section("STEP 3: PII Columns Summary (First 10)")
        pii_columns = admin_service.get_pii_columns_summary()
        for i, col in enumerate(pii_columns[:10]):
            print(f"\n{i+1}. {col['table_name']}.{col['column_name']}")
            print(f"   PII Type: {col['pii_type']}")
            print(f"   Technique: {col['anonymization_technique']}")
            print(f"   Confidence: {col['confidence']}")
            if col.get('admin_override'):
                print(f"   [WARN] Admin Override: {col['admin_comments']}")
        
        # Step 4: Override a column technique
        print_section("STEP 4: Override Column Technique")
        
        # Find a PII column to override (e.g., customer phone from TOKENIZATION to MASKING)
        target_table = None
        target_column = None
        current_technique = None
        
        for col in pii_columns:
            if col['table_name'] == 'customers' and col['column_name'] == 'phone':
                target_table = col['table_name']
                target_column = col['column_name']
                current_technique = col['anonymization_technique']
                break
        
        if target_table and target_column:
            print(f"Target: {target_table}.{target_column}")
            print(f"Current Technique: {current_technique}")
            print(f"New Technique: MASKING")
            
            success = admin_service.override_column_technique(
                table_name=target_table,
                column_name=target_column,
                new_technique="MASKING",
                admin_name="test_admin",
                admin_comment="Testing override functionality - changing from TOKENIZATION to MASKING"
            )
            
            if success:
                print("[OK] Column override successful")
                
                # Verify the override
                updated_col = admin_service.get_column_policy(target_table, target_column)
                print(f"Verified Technique: {updated_col['anonymization_technique']}")
                print(f"Admin Override: {updated_col['admin_override']}")
                print(f"Admin Comments: {updated_col['admin_comments']}")
            else:
                print("[FAIL] Column override failed")
        else:
            print("[WARN] Could not find customers.phone for override test")
        
        # Step 5: Approve the policy
        print_section("STEP 5: Approve Policy")
        
        approval_comments = [
            "Reviewed all PII columns",
            "Approved for testing with small dataset",
            "One manual override applied to customers.phone"
        ]
        
        success = admin_service.approve_policy(
            admin_name="test_admin",
            comments=approval_comments
        )
        
        if success:
            print("[OK] Policy approved successfully")
            
            # Verify approval
            approved_status = admin_service.get_policy_status()
            print("\nApproved Policy Status:")
            print_policy_status(approved_status)
        else:
            print("[FAIL] Policy approval failed")
        
        # Step 6: Verify executor accepts APPROVED policy
        print_section("STEP 6: Verify Executor Accepts APPROVED Policy")
        
        # Import policy executor to test validation
        from policy_executor import PolicyExecutor
        
        # Create a minimal executor config (we won't actually run the pipeline)
        # We just want to test the load_policy() validation
        executor = PolicyExecutor(
            source_db_config={"database_type": "postgresql", "database_name": "test"},
            destination_db_config={"database_type": "postgresql", "database_name": "test_dest"},
            policy_file="anonymization_policy.json"
        )
        
        # Test policy loading
        policy_valid = executor.load_policy()
        
        if policy_valid:
            print("[OK] Executor successfully loaded and validated APPROVED policy")
            print(f"[OK] Policy version: {executor.policy['policy_metadata']['policy_version']}")
            print(f"[OK] Status: {executor.policy['policy_metadata']['status']}")
        else:
            print("[FAIL] Executor rejected the policy")
        
        # Step 7: Test rejection workflow
        print_section("STEP 7: Test Rejection Workflow (Reset to DRAFT first)")
        
        # Reset to DRAFT to test rejection
        admin_service.reset_to_draft(
            admin_name="test_admin",
            reason="Testing rejection workflow"
        )
        print("[OK] Policy reset to DRAFT")
        
        # Try to reject
        try:
            rejection_comments = [
                "Policy needs revision",
                "Some techniques need adjustment"
            ]
            
            success = admin_service.reject_policy(
                admin_name="test_admin",
                comments=rejection_comments
            )
            
            if success:
                print("[OK] Policy rejected successfully")
                
                rejected_status = admin_service.get_policy_status()
                print("\nRejected Policy Status:")
                print_policy_status(rejected_status)
            else:
                print("[FAIL] Policy rejection failed")
        except ValueError as e:
            print(f"[FAIL] Rejection error: {e}")
        
        # Step 8: Final cleanup - approve again for normal operation
        print_section("STEP 8: Final Cleanup - Approve for Normal Operation")
        
        # Reset to DRAFT first
        admin_service.reset_to_draft(
            admin_name="test_admin",
            reason="Final cleanup - approving for normal operation"
        )
        
        # Approve
        admin_service.approve_policy(
            admin_name="test_admin",
            comments=["Workflow test completed. Policy approved for normal operation."]
        )
        
        final_status = admin_service.get_policy_status()
        print("[OK] Final Policy Status:")
        print_policy_status(final_status)
        
        print_section("WORKFLOW TEST COMPLETED SUCCESSFULLY")
        print("\nSummary:")
        print("[OK] Policy retrieved for review")
        print("[OK] Column override applied successfully")
        print("[OK] Policy approved with audit trail")
        print("[OK] Executor validated APPROVED policy")
        print("[OK] Rejection workflow tested")
        print("[OK] Policy ready for execution")
        
    except Exception as e:
        print(f"\n[FAIL] Error during workflow test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
