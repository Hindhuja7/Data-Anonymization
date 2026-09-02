"""
Test verification script for Step 14: Validation Engine & Thief Agent.
"""

import os
import sys
import json
import sqlite3
import time
from sqlalchemy import create_engine, text

# Add layers to path
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _layer in [
    "Connection_Extraction", "Enterprise_Classification", 
    "PII_Detection", "Change_Detection", 
    "Redis_Hash_Vault", "Redis_AOF_Safety", 
    "Polling_Worker", "Destination_Loader", 
    "Validation_Engine", "Audit_Report", 
    "Admin_Dashboard", "Approval_Workflow"
]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from policy_executor import PolicyExecutor
from validation_engine import ValidationEngine
from database_connector import DatabaseConnector

# DB paths
db_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "val_src.db")
db_dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "val_dst.db")
policy_clean = os.path.join(os.path.dirname(os.path.abspath(__file__)), "val_policy_clean.json")
policy_leak = os.path.join(os.path.dirname(os.path.abspath(__file__)), "val_policy_leak.json")

def create_source_db():
    if os.path.exists(db_src):
        try: os.remove(db_src)
        except Exception: pass
    if os.path.exists(db_dst):
        try: os.remove(db_dst)
        except Exception: pass
        
    conn = sqlite3.connect(db_src)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            full_name VARCHAR(100),
            aadhaar_no VARCHAR(20),
            email VARCHAR(100),
            comments TEXT
        )
    """)
    
    cursor.executemany("""
        INSERT INTO customers (customer_id, full_name, aadhaar_no, email, comments)
        VALUES (?, ?, ?, ?, ?)
    """, [
        (1, "Harish Nair", "1234 5678 9012", "harish.nair@gmail.com", "Safe notes here."),
        (2, "Neeta Sharma", "9876 5432 1098", "neeta@outlook.com", "Note: Aadhaar is 9876 5432 1098 (leaked inside notes)."),
        (3, "John Doe", "1111 2222 3333", "john.doe@example.com", "No issues.")
    ])
    
    conn.commit()
    conn.close()
    print("[OK] Source DB initialized with test records.")

def create_policies():
    # Clean Policy (Anonymizes all PII)
    clean = {
        "policy_metadata": {
            "policy_version": "1.0",
            "status": "APPROVED",
            "approved_by": "Admin"
        },
        "column_policies": [
            {
                "table_name": "customers", "column_name": "customer_id",
                "is_pii": True, "pii_type": "IDENTIFIER",
                "anonymization_technique": "HASHING", "data_type": "INTEGER"
            },
            {
                "table_name": "customers", "column_name": "full_name",
                "is_pii": True, "pii_type": "NAME",
                "anonymization_technique": "TOKENIZATION", "data_type": "VARCHAR(100)"
            },
            {
                "table_name": "customers", "column_name": "aadhaar_no",
                "is_pii": True, "pii_type": "AADHAAR",
                "anonymization_technique": "MASKING", "data_type": "VARCHAR(20)"
            },
            {
                "table_name": "customers", "column_name": "email",
                "is_pii": True, "pii_type": "EMAIL",
                "anonymization_technique": "TOKENIZATION", "data_type": "VARCHAR(100)"
            },
            {
                "table_name": "customers", "column_name": "comments",
                "is_pii": True, "pii_type": "QUASI_IDENTIFIER",
                "anonymization_technique": "MASKING", "data_type": "TEXT" # Mask comments to cover PII
            }
        ]
    }
    
    # Leak Policy (Intentionally leaves full_name and comments as NO_CHANGE)
    leak = {
        "policy_metadata": {
            "policy_version": "1.0",
            "status": "APPROVED",
            "approved_by": "Admin"
        },
        "column_policies": [
            {
                "table_name": "customers", "column_name": "customer_id",
                "is_pii": True, "pii_type": "IDENTIFIER",
                "anonymization_technique": "HASHING", "data_type": "INTEGER"
            },
            {
                "table_name": "customers", "column_name": "full_name",
                "is_pii": True, "pii_type": "NAME",
                "anonymization_technique": "NO_CHANGE", "data_type": "VARCHAR(100)" # Leak Name!
            },
            {
                "table_name": "customers", "column_name": "aadhaar_no",
                "is_pii": True, "pii_type": "AADHAAR",
                "anonymization_technique": "MASKING", "data_type": "VARCHAR(20)"
            },
            {
                "table_name": "customers", "column_name": "email",
                "is_pii": True, "pii_type": "EMAIL",
                "anonymization_technique": "TOKENIZATION", "data_type": "VARCHAR(100)"
            },
            {
                "table_name": "customers", "column_name": "comments",
                "is_pii": True, "pii_type": "QUASI_IDENTIFIER",
                "anonymization_technique": "NO_CHANGE", "data_type": "TEXT" # Leak comments containing Aadhaar!
            }
        ]
    }
    
    with open(policy_clean, "w") as f:
        json.dump(clean, f, indent=2)
    with open(policy_leak, "w") as f:
        json.dump(leak, f, indent=2)
    print("[OK] Test policies generated.")

def run_test_scenario(policy_file: str, scenario_name: str) -> bool:
    print(f"\n================================================================================")
    print(f"RUNNING scenario: {scenario_name}")
    print(f"================================================================================")
    
    if os.path.exists(db_dst):
        try: os.remove(db_dst)
        except Exception: pass
        
    src_config = {"database_type": "sqlite", "database_name": db_src}
    dst_config = {"database_type": "sqlite", "database_name": db_dst}
    
    executor = PolicyExecutor(
        source_db_config=src_config,
        destination_db_config=dst_config,
        policy_file=policy_file,
        chunk_size=10,
        redis_host="localhost",
        redis_port=6379,
        hmac_secret="secret-123"
    )
    
    # Run the execution (includes schema validation and results validation)
    success = executor.execute()
    executor.cleanup()
    return success

def main():
    print("=" * 80)
    print("STEP 14 VALIDATION ENGINE END-TO-END TEST")
    print("=" * 80)
    
    create_source_db()
    create_policies()
    
    # 1. Run Clean Scenario (Anonymized correctly)
    clean_passed = run_test_scenario(policy_clean, "CLEAN ANONYMIZATION")
    
    # 2. Run Leak Scenario (Names and Aadhaar comments left unanonymized)
    leak_passed = run_test_scenario(policy_leak, "LEAKY ANONYMIZATION (PII EXPOSED)")
    
    # Assertions
    assert clean_passed is True, "Clean anonymization was flagged as insecure"
    assert leak_passed is False, "Leaky anonymization was allowed to pass validation!"
    
    # Cleanup DB files
    time.sleep(0.5)
    for f in [db_src, db_dst, policy_clean, policy_leak]:
        if os.path.exists(f):
            try: os.remove(f)
            except Exception: pass
            
    print("\n" + "=" * 80)
    print("[ALL PASSED] Step 14 Validation Engine verified successfully!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
