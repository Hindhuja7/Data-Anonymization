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
    # Check customers table
    result = connection.execute(text("SELECT COUNT(*) FROM customers"))
    print(f"Source customers count: {result.fetchone()[0]}")

    # Check accounts.customer_id FK integrity
    result = connection.execute(text("""
        SELECT COUNT(*)
        FROM accounts a
        LEFT JOIN customers c ON a.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
    """))
    orphaned = result.fetchone()[0]
    print(f"Accounts with orphaned customer_id: {orphaned}")

    # Check total accounts
    result = connection.execute(text("SELECT COUNT(*) FROM accounts"))
    print(f"Total accounts: {result.fetchone()[0]}")

conn.disconnect()
