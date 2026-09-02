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

    print("Transactions with account_id not in accounts table:")
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
    print(f"\nTotal orphaned transactions: {total}")

    # Check total transactions
    result = connection.execute(text("SELECT COUNT(*) FROM transactions"))
    total_transactions = result.fetchone()[0]
    print(f"Total transactions: {total_transactions}")

conn.disconnect()
