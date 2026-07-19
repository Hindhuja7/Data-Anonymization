"""
Test verification script for AdminPolicyService risk forecast.
"""

import os
import sys
import json

# Path bootstrapper to allow flat imports across layers
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _layer in ["11_Admin_Dashboard", "03_PII_Detection"]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from admin_policy_service import AdminPolicyService

def main():
    print("=" * 80)
    print("RUNNING ADMIN POLICY REVIEW RISK FORECAST TEST")
    print("=" * 80)
    
    test_policy_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_policy.json")
    
    # 1. Create a proposed DRAFT policy where full_name is raw (leaking)
    proposed_policy = {
        "policy_metadata": {
            "policy_version": "1.0",
            "status": "DRAFT",
            "generated_at": "2026-07-19T18:00:00Z"
        },
        "column_policies": [
            {
                "table_name": "employees", "column_name": "employee_id",
                "is_pii": True, "pii_type": "IDENTIFIER",
                "anonymization_technique": "HASHING"
            },
            {
                "table_name": "employees", "column_name": "full_name",
                "is_pii": True, "pii_type": "NAME",
                "anonymization_technique": "NO_CHANGE"  # This will trigger a risk score penalty!
            }
        ]
    }
    
    with open(test_policy_path, "w") as f:
        json.dump(proposed_policy, f, indent=2)
    print(f"[OK] Draft policy saved to {test_policy_path}")
    
    # Initialize policy review service
    service = AdminPolicyService(policy_file=test_policy_path)
    
    # 2. Get policy review metadata (Pre-Execution Audit)
    print("\nRequesting policy review metadata...")
    review = service.get_policy_for_review()
    
    metadata = review["review_metadata"]
    forecast = metadata["risk_forecast"]
    
    print("\n--- Predicted Risk Assessment (Before override) ---")
    print(f"Predicted Score : {forecast['predicted_risk_score']} / 100")
    print(f"Risk Flag Color : {forecast['risk_flag']}")
    print(f"Vulnerabilities : {forecast['vulnerabilities']}")
    print(f"Legend Note     : {forecast['legend'][forecast['risk_flag']]}")
    
    assert forecast["predicted_risk_score"] > 0, "Risk score should be greater than 0 due to NO_CHANGE!"
    assert forecast["risk_flag"] in ["YELLOW", "RED"], "Flag color should be Yellow or Red!"
    print("[OK] Risk forecast correctly identified the raw name leak.")
    
    # 3. Admin corrects the policy in memory (Overrides NO_CHANGE -> TOKENIZATION)
    print("\nAdmin correcting override in memory: NO_CHANGE -> TOKENIZATION...")
    override_success = service.override_column_technique(
        table_name="employees",
        column_name="full_name",
        new_technique="TOKENIZATION",
        admin_name="Compliance Manager Alice",
        admin_comment="Corrected leak to use tokenization."
    )
    assert override_success, "Override failed!"
    print("[OK] Column corrected successfully.")
    
    # 4. Re-evaluate forecast
    review_after = service.get_policy_for_review()
    forecast_after = review_after["review_metadata"]["risk_forecast"]
    
    print("\n--- Predicted Risk Assessment (After override) ---")
    print(f"Predicted Score : {forecast_after['predicted_risk_score']} / 100")
    print(f"Risk Flag Color : {forecast_after['risk_flag']}")
    print(f"Vulnerabilities : {forecast_after['vulnerabilities']}")
    print(f"Legend Note     : {forecast_after['legend'][forecast_after['risk_flag']]}")
    
    assert forecast_after["predicted_risk_score"] == 0.0, "Risk score should drop to 0.0!"
    assert forecast_after["risk_flag"] == "GREEN", "Flag color should return to GREEN!"
    print("[OK] Risk score successfully dropped to 0.0 (GREEN).")
    
    # Cleanup
    if os.path.exists(test_policy_path):
        os.remove(test_policy_path)
        
    print("\n[ALL PASSED] Pre-execution audit review test completed successfully!")

if __name__ == "__main__":
    main()
