"""
Test verification script for AuditReportGenerator.
"""

import os
import sys
import json
import shutil
from datetime import datetime

# Path bootstrapper to allow flat imports across layers
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _layer in ["Audit_Report", "Validation_Engine"]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from audit_report_generator import AuditReportGenerator

def main():
    print("=" * 80)
    print("RUNNING COMPLIANCE REPORT GENERATOR VERIFICATION TEST")
    print("=" * 80)
    
    # Mock Policy
    mock_policy = {
        "policy_metadata": {
            "policy_version": "2.4",
            "status": "APPROVED",
            "approved_by": "System Admin"
        },
        "column_policies": [
            {
                "table_name": "employees", "column_name": "employee_id",
                "is_pii": True, "pii_type": "IDENTIFIER",
                "anonymization_technique": "HASHING"
            },
            {
                "table_name": "employees", "column_name": "full_name",
                "is_pii": True, "pii_type": "FULL_NAME",
                "anonymization_technique": "TOKENIZATION"
            },
            {
                "table_name": "employees", "column_name": "aadhaar",
                "is_pii": True, "pii_type": "AADHAAR",
                "anonymization_technique": "MASKING"
            },
            {
                "table_name": "employees", "column_name": "salary",
                "is_pii": True, "pii_type": "FINANCIAL",
                "anonymization_technique": "DIFFERENTIAL_PRIVACY"
            }
        ]
    }
    
    # Mock Validation Results
    mock_table_reports = [
        {
            "table_name": "employees",
            "row_counts_match": True,
            "checks_passed": True,
            "risk_score": 0.0,
            "leaks": [],
            "thief_report": {
                "anonymization_broken": False,
                "risk_severity": "LOW",
                "vulnerability_details": "All quasi-identifiers are fully obfuscated. No linkages possible."
            }
        }
    ]
    
    # Mock Execution Summary Stats
    mock_exec_stats = {
        "duration_seconds": 12.45,
        "tables_processed": 1,
        "total_rows_processed": 5000
    }
    
    # Temporary test output folder inside current folder
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_report_test_output")
    
    # Initialize report generator
    generator = AuditReportGenerator(policy=mock_policy, compliance_law="DPDP Act 2023")
    
    # Generate reports
    print("Generating compliance report files...")
    report_data = generator.generate_report(
        table_reports=mock_table_reports,
        execution_stats=mock_exec_stats,
        output_dir=output_dir,
        approved_by="Compliance Officer Alice"
    )
    
    json_file = os.path.join(output_dir, "compliance_report.json")
    txt_file = os.path.join(output_dir, "compliance_report.txt")
    
    # Verify files were generated
    assert os.path.exists(json_file), "JSON compliance report not created!"
    assert os.path.exists(txt_file), "Text certificate not created!"
    print("[OK] Both report files successfully created.")
    
    # Verify content
    with open(json_file, "r") as f:
        data = json.load(f)
        
    assert data["compliance_metadata"]["overall_privacy_risk_score"] == 0.0, "Overall score mismatch!"
    assert data["compliance_metadata"]["auditor_signature"] == "Compliance Officer Alice", "Auditor signature mismatch!"
    assert data["execution_summary"]["total_rows_anonymized"] == 5000, "Rows processed mismatch!"
    print("[OK] JSON compliance data assertions passed.")
    
    print("\n" + "=" * 80)
    print("GENERATED HUMAN-READABLE TEXT COMPLIANCE CERTIFICATE:")
    print("=" * 80)
    with open(txt_file, "r", encoding="utf-8") as f:
        print(f.read())
    print("=" * 80)
    
    # Cleanup output directory
    shutil.rmtree(output_dir)
    print("\n[ALL PASSED] Audit report verification test completed successfully!")

if __name__ == "__main__":
    main()
