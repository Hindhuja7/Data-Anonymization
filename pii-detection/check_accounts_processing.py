from database_connector import DatabaseConnector
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

conn = DatabaseConnector(
    database_type=os.getenv('SOURCE_DB_TYPE'),
    host=os.getenv('SOURCE_DB_HOST'),
    port=int(os.getenv('SOURCE_DB_PORT')),
    username=os.getenv('SOURCE_DB_USERNAME'),
    password=os.getenv('SOURCE_DB_PASSWORD'),
    database_name=os.getenv('SOURCE_DB_NAME')
)
engine = conn.connect()

with engine.connect() as connection:
    # Check if accounts table has any VARCHAR columns that might cause truncation
    result = connection.execute(text("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'accounts' 
        AND data_type LIKE 'character%'
        ORDER BY ordinal_position
    """))

    print("Accounts table VARCHAR columns:")
    for row in result:
        print(f"  {row[0]}: {row[1]}({row[2] if row[2] else 'N/A'})")

    # Check sample data for varchar columns
    print("\nSample data from accounts:")
    result = connection.execute(text("""
        SELECT account_type, ifsc_code, branch_name, gstin
        FROM accounts
        LIMIT 5
    """))
    for row in result:
        print(f"  account_type: {row[0]} (len: {len(row[0]) if row[0] else 0})")
        print(f"  ifsc_code: {row[1]} (len: {len(row[1]) if row[1] else 0})")
        print(f"  branch_name: {row[2]} (len: {len(row[2]) if row[2] else 0})")
        print(f"  gstin: {row[3]} (len: {len(row[3]) if row[3] else 0})")
        print()

conn.disconnect()
