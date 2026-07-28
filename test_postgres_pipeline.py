"""
Test 17-step pipeline with PostgreSQL using terminal approval
"""

import os
import sys
from dotenv import load_dotenv

# Add Destination_Loader to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Destination_Loader"))

from policy_executor import PolicyExecutor

def test_postgres_pipeline(single_table=True):
    """Test pipeline with PostgreSQL and terminal approval"""
    print("="*60)
    print("17-STEP PIPELINE TEST - POSTGRESQL")
    print("="*60)
    
    if single_table:
        print("Mode: Single table testing (customers only)")
    else:
        print("Mode: Full pipeline testing")
    
    load_dotenv()
    
    # Source database configuration
    source_db_config = {
        "database_type": os.getenv("SOURCE_DB_TYPE", "postgresql"),
        "host": os.getenv("SOURCE_DB_HOST"),
        "port": int(os.getenv("SOURCE_DB_PORT", 5432)),
        "username": os.getenv("SOURCE_DB_USERNAME"),
        "password": os.getenv("SOURCE_DB_PASSWORD"),
        "database_name": os.getenv("SOURCE_DB_NAME"),
        "sslmode": os.getenv("SOURCE_DB_SSLMODE")
    }
    
    # Destination database configuration
    destination_db_config = {
        "database_type": os.getenv("DEST_DB_TYPE", "postgresql"),
        "host": os.getenv("DEST_DB_HOST"),
        "port": int(os.getenv("DEST_DB_PORT", 5432)),
        "username": os.getenv("DEST_DB_USERNAME"),
        "password": os.getenv("DEST_DB_PASSWORD"),
        "database_name": os.getenv("DEST_DB_NAME"),
        "sslmode": os.getenv("DEST_DB_SSLMODE")
    }
    
    print("\nSource Database:")
    print(f"  Type: {source_db_config['database_type']}")
    print(f"  Host: {source_db_config['host']}:{source_db_config['port']}")
    print(f"  Database: {source_db_config['database_name']}")
    
    print("\nDestination Database:")
    print(f"  Type: {destination_db_config['database_type']}")
    print(f"  Host: {destination_db_config['host']}:{destination_db_config['port']}")
    print(f"  Database: {destination_db_config['database_name']}")
    
    print("\n" + "="*60)
    print("Starting Pipeline Execution")
    print("="*60)
    
    try:
        executor = PolicyExecutor(
            source_db_config=source_db_config,
            destination_db_config=destination_db_config,
            policy_file=None,  # Will generate new policy
            chunk_size=int(os.getenv("CHUNK_SIZE", 10)),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", 6379)),
            hmac_secret=os.getenv("HMAC_SECRET")
        )
        
        # Filter to single table if requested
        if single_table:
            executor.single_table_mode = True
            executor.single_table_name = "customers"
            print(f"✓ Single table mode: Will process only 'customers' table")
        
        success = executor.execute()
        
        print("\n" + "="*60)
        print("PIPELINE EXECUTION RESULT")
        print("="*60)
        
        if success:
            print("✓ Pipeline completed successfully")
            print(f"  Steps completed: {executor.context.completed_steps}")
            print(f"  Tables processed: {len(executor.context.tables_processed)}")
            print(f"  Total rows processed: {executor.context.total_rows_processed}")
            return 0
        else:
            print("✗ Pipeline failed")
            print(f"  Failed at step: {executor.context.get_current_step()}")
            if executor.context.errors:
                print(f"  Last error: {executor.context.errors[-1]}")
            return 1
            
    except Exception as e:
        print(f"✗ Pipeline execution error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(test_postgres_pipeline())
