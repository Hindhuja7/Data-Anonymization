import os
import sys
from dotenv import load_dotenv
from policy_executor import PolicyExecutor

load_dotenv()

# Source database configuration
source_db_config = {
    "database_type": os.getenv("SOURCE_DB_TYPE", "postgresql"),
    "host": os.getenv("SOURCE_DB_HOST"),
    "port": int(os.getenv("SOURCE_DB_PORT", 5432)),
    "username": os.getenv("SOURCE_DB_USERNAME"),
    "password": os.getenv("SOURCE_DB_PASSWORD"),
    "database_name": os.getenv("SOURCE_DB_NAME"),
    "sslmode": os.getenv("SOURCE_DB_SSLMODE", "require")
}

# Destination database configuration
destination_db_config = {
    "database_type": os.getenv("DEST_DB_TYPE", "postgresql"),
    "host": os.getenv("DEST_DB_HOST"),
    "port": int(os.getenv("DEST_DB_PORT", 5432)),
    "username": os.getenv("DEST_DB_USERNAME"),
    "password": os.getenv("DEST_DB_PASSWORD"),
    "database_name": os.getenv("DEST_DB_NAME"),
    "sslmode": os.getenv("DEST_DB_SSLMODE", "require")
}

# Initialize executor with very small chunk size
executor = PolicyExecutor(
    source_db_config=source_db_config,
    destination_db_config=destination_db_config,
    policy_file="anonymization_policy.json",
    chunk_size=5,  # Very small chunk
    redis_host=os.getenv("REDIS_HOST", "localhost"),
    redis_port=int(os.getenv("REDIS_PORT", 6379)),
    hmac_secret=os.getenv("HMAC_SECRET"),
    destination_table_prefix=""
)

try:
    # Load policy
    if not executor.load_policy():
        sys.exit(1)
    
    # Connect
    if not executor.connect_databases():
        sys.exit(1)
    
    # Get schema
    executor.get_source_schema()
    
    # Create schema
    if not executor.create_destination_schema():
        sys.exit(1)
    
    # Process only accounts table
    print("\nProcessing accounts table only...")
    success = executor.process_table("accounts")
    
    print(f"\nAccounts table processing: {'SUCCESS' if success else 'FAILED'}")
    
    # Check destination
    dest_count = executor.get_destination_table_row_count("accounts")
    print(f"Destination accounts count: {dest_count}")
    
    executor.cleanup()
    sys.exit(0 if success and dest_count > 0 else 1)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    executor.cleanup()
    sys.exit(1)
