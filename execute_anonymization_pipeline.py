"""
Main Entry Point for Anonymization Pipeline Execution

This script executes the approved anonymization policy on the source database
and writes the anonymized data to a destination database.
"""

import os
import sys
from dotenv import load_dotenv

# Path bootstrapper to allow flat imports across layers
_root = os.path.dirname(os.path.abspath(__file__))
for _layer in ["Layer_1_Connection_Extraction", "Layer_2_Enterprise_Classification", "Layer_3_PII_Detection", "Layer_4_Anonymization_Vault"]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from policy_executor import PolicyExecutor

load_dotenv()


def main():
    """Main execution function."""
    
    # Source database configuration (read-only)
    source_db_config = {
        "database_type": os.getenv("SOURCE_DB_TYPE", "postgresql"),
        "host": os.getenv("SOURCE_DB_HOST"),
        "port": int(os.getenv("SOURCE_DB_PORT", 5432)),
        "username": os.getenv("SOURCE_DB_USERNAME"),
        "password": os.getenv("SOURCE_DB_PASSWORD"),
        "database_name": os.getenv("SOURCE_DB_NAME"),
        "sslmode": os.getenv("SOURCE_DB_SSLMODE", "require")
    }
    
    # Destination database configuration (write access)
    destination_db_config = {
        "database_type": os.getenv("DEST_DB_TYPE", "postgresql"),
        "host": os.getenv("DEST_DB_HOST"),
        "port": int(os.getenv("DEST_DB_PORT", 5432)),
        "username": os.getenv("DEST_DB_USERNAME"),
        "password": os.getenv("DEST_DB_PASSWORD"),
        "database_name": os.getenv("DEST_DB_NAME"),
        "sslmode": os.getenv("DEST_DB_SSLMODE", "require")
    }
    
    # Policy configuration
    policy_file = os.getenv("POLICY_FILE", "anonymization_policy.json")
    chunk_size = int(os.getenv("CHUNK_SIZE", 10))  # Default 10 for testing
    
    # Redis configuration
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    hmac_secret = os.getenv("HMAC_SECRET")
    
    print("=" * 80)
    print("ANONYMIZATION PIPELINE EXECUTION")
    print("=" * 80)
    print(f"\nSource Database: {source_db_config['database_name']}")
    print(f"Destination Database: {destination_db_config['database_name']}")
    print(f"Policy File: {policy_file}")
    print(f"Chunk Size: {chunk_size:,} rows")
    print(f"Redis: {redis_host}:{redis_port}")
    
    # Validate required source environment variables
    required_source_vars = ["SOURCE_DB_HOST", "SOURCE_DB_USERNAME", "SOURCE_DB_PASSWORD", "SOURCE_DB_NAME"]
    missing_vars = [var for var in required_source_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\nERROR: Missing required source environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        sys.exit(1)
    
    # Validate required destination environment variables
    required_dest_vars = ["DEST_DB_HOST", "DEST_DB_USERNAME", "DEST_DB_PASSWORD", "DEST_DB_NAME"]
    missing_vars = [var for var in required_dest_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\nERROR: Missing required destination environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        sys.exit(1)
    
    # Validate that source and destination are different databases
    # Check full connection identity (host + port + database name)
    if (source_db_config['host'] == destination_db_config['host'] and
        source_db_config['port'] == destination_db_config['port'] and
        source_db_config['database_name'] == destination_db_config['database_name']):
        print(f"\nERROR: Source and destination point to the same database:")
        print(f"  Host: {source_db_config['host']}")
        print(f"  Port: {source_db_config['port']}")
        print(f"  Database: {source_db_config['database_name']}")
        print("The destination must be a completely separate database.")
        print("Please set DEST_DB_HOST, DEST_DB_PORT, or DEST_DB_NAME to different values.")
        sys.exit(1)
    
    # Check if policy file exists
    if not os.path.exists(policy_file):
        print(f"\nERROR: Policy file not found: {policy_file}")
        print("Please run policy generation first: python test_policy_generation.py")
        sys.exit(1)
    
    # Initialize executor
    executor = PolicyExecutor(
        source_db_config=source_db_config,
        destination_db_config=destination_db_config,
        policy_file=policy_file,
        chunk_size=chunk_size,
        redis_host=redis_host,
        redis_port=redis_port,
        hmac_secret=hmac_secret,
        destination_table_prefix=""  # No prefix - use original table names
    )
    
    try:
        # Execute the pipeline
        success = executor.execute()
        
        # Cleanup
        executor.cleanup()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user")
        executor.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        executor.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
