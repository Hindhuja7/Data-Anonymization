"""
Test script for Anonymization Policy Generation
Demonstrates the policy generation workflow
"""

import os
import sys
import json
from dotenv import load_dotenv

from database_pii_detection import DatabasePIIDetector

load_dotenv()

def test_policy_generation():
    """Test the complete policy generation workflow."""
    print("=" * 80)
    print("ANONYMIZATION POLICY GENERATION TEST")
    print("=" * 80)
    
    # Initialize detector
    detector = DatabasePIIDetector(
        database_type=os.getenv("DB_TYPE", "postgresql"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        username=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        database_name=os.getenv("DB_NAME"),
        provider=os.getenv("LLM_PROVIDER", "github"),
        model=os.getenv("LLM_MODEL", "gpt-4o")
    )
    
    try:
        # Step 1: Connect to database
        print("\n[STEP 1] Connecting to database...")
        detector.connect()
        print(f"✓ Connected to {detector.database_name}")
        
        # Step 2: Run PII detection
        print("\n[STEP 2] Running PII detection...")
        pii_report = detector.detect_pii()
        print(f"✓ PII detection completed")
        print(f"  - Enterprise type: {pii_report['enterprise_type']}")
        print(f"  - Tables scanned: {len(pii_report['tables'])}")
        
        # Step 3: Generate anonymization policy
        print("\n[STEP 3] Generating anonymization policy...")
        policy = detector.generate_anonymization_policy(
            pii_report=pii_report,
            output_file="anonymization_policy.json"
        )
        print(f"✓ Policy generated and saved to anonymization_policy.json")
        
        # Step 4: Display policy summary
        print("\n[STEP 4] Policy Summary:")
        print("-" * 80)
        summary = policy["policy_summary"]
        print(f"Total columns: {summary['total_columns']}")
        print(f"PII columns: {summary['pii_columns']} ({summary['pii_percentage']}%)")
        print(f"Non-PII columns: {summary['non_pii_columns']}")
        print(f"\nTechnique distribution:")
        for technique, count in summary['technique_distribution'].items():
            print(f"  - {technique}: {count}")
        
        print(f"\nPII type distribution:")
        for pii_type, count in summary['pii_type_distribution'].items():
            print(f"  - {pii_type}: {count}")
        
        # Step 5: Show sample policy entries
        print("\n[STEP 5] Sample Policy Entries:")
        print("-" * 80)
        for i, column_policy in enumerate(policy["column_policies"][:5]):
            print(f"\n{i+1}. {column_policy['table_name']}.{column_policy['column_name']}")
            print(f"   Is PII: {column_policy['is_pii']}")
            print(f"   PII Type: {column_policy['pii_type']}")
            print(f"   Confidence: {column_policy['confidence']}")
            print(f"   Technique: {column_policy['anonymization_technique']}")
            print(f"   Reason: {column_policy['reason'][:100]}...")
        
        print("\n" + "=" * 80)
        print("POLICY GENERATION TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Review anonymization_policy.json")
        print("2. Admin can modify techniques or add comments")
        print("3. Approve policy for execution")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        detector.disconnect()


if __name__ == "__main__":
    test_policy_generation()
