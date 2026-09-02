from database_connector import DatabaseConnector
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

# Check source
source_conn = DatabaseConnector(
    database_type=os.getenv('SOURCE_DB_TYPE'),
    host=os.getenv('SOURCE_DB_HOST'),
    port=int(os.getenv('SOURCE_DB_PORT')),
    username=os.getenv('SOURCE_DB_USERNAME'),
    password=os.getenv('SOURCE_DB_PASSWORD'),
    database_name=os.getenv('SOURCE_DB_NAME')
)
source_engine = source_conn.connect()

# Check destination
dest_conn = DatabaseConnector(
    database_type=os.getenv('DEST_DB_TYPE'),
    host=os.getenv('DEST_DB_HOST'),
    port=int(os.getenv('DEST_DB_PORT')),
    username=os.getenv('DEST_DB_USERNAME'),
    password=os.getenv('DEST_DB_PASSWORD'),
    database_name=os.getenv('DEST_DB_NAME')
)
dest_engine = dest_conn.connect()

# Problem account_ids from error
problem_account_ids = [49012, 34217, 39579]

print("Checking problem account_ids in source vs destination:")
for acc_id in problem_account_ids:
    # Source
    with source_engine.connect() as conn:
        result = conn.execute(text(f"SELECT account_id FROM accounts WHERE account_id = {acc_id}"))
        source_exists = result.fetchone() is not None
    
    # Destination
    with dest_engine.connect() as conn:
        result = conn.execute(text(f"SELECT account_id FROM accounts WHERE account_id = {acc_id}"))
        dest_exists = result.fetchone() is not None
    
    print(f"  account_id {acc_id}: Source={source_exists}, Dest={dest_exists}")

# Check sample account_ids from source
print("\nSample account_ids from source accounts:")
with source_engine.connect() as conn:
    result = conn.execute(text("SELECT account_id FROM accounts ORDER BY account_id LIMIT 10"))
    for row in result:
        print(f"  {row[0]}")

# Check sample account_ids from destination
print("\nSample account_ids from destination accounts:")
with dest_engine.connect() as conn:
    result = conn.execute(text("SELECT account_id FROM accounts ORDER BY account_id LIMIT 10"))
    for row in result:
        print(f"  {row[0]}")

source_conn.disconnect()
dest_conn.disconnect()
