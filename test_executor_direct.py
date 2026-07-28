"""
Direct test of PolicyExecutor without API layer
Tests the 17-step pipeline execution directly
"""

import os
import sys
from dotenv import load_dotenv

# Load test environment
load_dotenv(".env.test")

# Add path for imports
_root = os.path.dirname(os.path.abspath(__file__))
for _layer in ["Connection_Extraction", "Enterprise_Classification", "PII_Detection", "Change_Detection", "Redis_Hash_Vault", "Redis_AOF_Safety", "Polling_Worker", "Destination_Loader", "Validation_Engine", "Audit_Report", "Admin_Dashboard", "Approval_Workflow"]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from policy_executor import PolicyExecutor

def test_executor_direct():
    """Test PolicyExecutor directly with test database"""
    
    print("="*60)
    print("DIRECT POLICY EXECUTOR TEST")
    print("="*60)
    
    # Source database configuration
    source_db_config = {
        "database_type": "sqlite",
        "host": None,
        "port": None,
        "username": None,
        "password": None,
        "database_name": "test_source.db",
        "sslmode": None
    }
    
    # Destination database configuration
    destination_db_config = {
        "database_type": "sqlite",
        "host": None,
        "port": None,
        "username": None,
        "password": None,
        "database_name": "test_destination.db",
        "sslmode": None
    }
    
    # Create a simple policy file for testing
    import json
    test_policy = {
        "policy_metadata": {
            "created_at": "2024-01-01",
            "approved_by": "TestAdmin",
            "approved": True,
            "status": "APPROVED"  # Set status to APPROVED to skip Step 7 waiting
        },
        "column_policies": {},
        "tables": {
            "customers": {
                "columns": {
                    "id": {"action": "keep"},
                    "name": {"action": "keep"},
                    "email": {"action": "hash"},
                    "phone": {"action": "mask"},
                    "address": {"action": "keep"}
                }
            },
            "orders": {
                "columns": {
                    "id": {"action": "keep"},
                    "customer_id": {"action": "keep"},
                    "order_date": {"action": "keep"},
                    "amount": {"action": "keep"}
                }
            },
            "order_items": {
                "columns": {
                    "id": {"action": "keep"},
                    "order_id": {"action": "keep"},
                    "product_name": {"action": "keep"},
                    "quantity": {"action": "keep"},
                    "price": {"action": "keep"}
                }
            }
        }
    }
    
    with open("test_policy.json", "w") as f:
        json.dump(test_policy, f, indent=2)
    
    print("\nTest policy created: test_policy.json")
    
    # Initialize executor
    executor = PolicyExecutor(
        source_db_config=source_db_config,
        destination_db_config=destination_db_config,
        policy_file="test_policy.json",
        chunk_size=2,
        redis_host="localhost",
        redis_port=6379,
        hmac_secret="test-hmac-secret",
        destination_table_prefix=""
    )
    
    # Pre-load the test policy to avoid Step 6 regeneration
    executor.policy = test_policy
    
    print("\nExecutor initialized")
    print(f"Source DB: {source_db_config['database_name']}")
    print(f"Destination DB: {destination_db_config['database_name']}")
    print(f"Chunk size: 2")
    
    # Execute the pipeline
    print("\n" + "="*60)
    print("EXECUTING 17-STEP PIPELINE")
    print("="*60)
    
    try:
        success = executor.execute()
        
        print("\n" + "="*60)
        print("PIPELINE EXECUTION RESULT")
        print("="*60)
        print(f"Success: {success}")
        
        # Print step summary
        print("\nStep Summary:")
        for step_num, step_info in executor.context.steps.items():
            status = step_info["status"].value if hasattr(step_info["status"], 'value') else str(step_info["status"])
            print(f"  Step {step_num}: {step_info['name']} - {status}")
        
        # Print progress
        print(f"\nProgress: {executor.context.get_progress_percentage():.1f}%")
        print(f"Tables processed: {len(executor.context.tables_processed)}")
        print(f"Total rows processed: {executor.context.total_rows_processed}")
        
        if success:
            print("\n✓ Pipeline completed successfully")
            return 0
        else:
            print("\n✗ Pipeline failed")
            return 1
            
    except Exception as e:
        print(f"\n✗ Pipeline execution error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_executor_direct())
