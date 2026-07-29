from database_connector import DatabaseConnector
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

conn = DatabaseConnector(
    database_type=os.getenv('DEST_DB_TYPE'),
    host=os.getenv('DEST_DB_HOST'),
    port=int(os.getenv('DEST_DB_PORT')),
    username=os.getenv('DEST_DB_USERNAME'),
    password=os.getenv('DEST_DB_PASSWORD'),
    database_name=os.getenv('DEST_DB_NAME')
)
engine = conn.connect()

with engine.connect() as connection:
    # Check for transactions with account_id not in accounts
    result = connection.execute(text("""
        SELECT t.account_id, COUNT(*) as count
        FROM transactions t
        LEFT JOIN accounts a ON t.account_id = a.account_id
        WHERE a.account_id IS NULL
        GROUP BY t.account_id
        ORDER BY count DESC
        LIMIT 10
    """))

    print("Transactions with account_id not in accounts table (destination):")
    for row in result:
        print(f"  account_id {row[0]}: {row[1]} transactions")

    # Get total count
    result = connection.execute(text("""
        SELECT COUNT(*)
        FROM transactions t
        LEFT JOIN accounts a ON t.account_id = a.account_id
        WHERE a.account_id IS NULL
    """))
    total = result.fetchone()[0]
    print(f"\nTotal orphaned transactions in destination: {total}")

conn.disconnect()
