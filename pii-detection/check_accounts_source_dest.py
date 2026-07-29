from database_connector import DatabaseConnector
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

# Source
source_conn = DatabaseConnector(
    database_type=os.getenv('SOURCE_DB_TYPE'),
    host=os.getenv('SOURCE_DB_HOST'),
    port=int(os.getenv('SOURCE_DB_PORT')),
    username=os.getenv('SOURCE_DB_USERNAME'),
    password=os.getenv('SOURCE_DB_PASSWORD'),
    database_name=os.getenv('SOURCE_DB_NAME')
)
source_engine = source_conn.connect()

# Destination
dest_conn = DatabaseConnector(
    database_type=os.getenv('DEST_DB_TYPE'),
    host=os.getenv('DEST_DB_HOST'),
    port=int(os.getenv('DEST_DB_PORT')),
    username=os.getenv('DEST_DB_USERNAME'),
    password=os.getenv('DEST_DB_PASSWORD'),
    database_name=os.getenv('DEST_DB_NAME')
)
dest_engine = dest_conn.connect()

print("Source accounts count:")
with source_engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM accounts"))
    print(f"  {result.fetchone()[0]}")

print("\nDestination accounts count:")
with dest_engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM accounts"))
    print(f"  {result.fetchone()[0]}")

print("\nSource account_id range:")
with source_engine.connect() as conn:
    result = conn.execute(text("SELECT MIN(account_id), MAX(account_id) FROM accounts"))
    row = result.fetchone()
    print(f"  Min: {row[0]}, Max: {row[1]}")

print("\nDestination account_id range:")
with dest_engine.connect() as conn:
    result = conn.execute(text("SELECT MIN(account_id), MAX(account_id) FROM accounts"))
    row = result.fetchone()
    print(f"  Min: {row[0]}, Max: {row[1]}")

source_conn.disconnect()
dest_conn.disconnect()
