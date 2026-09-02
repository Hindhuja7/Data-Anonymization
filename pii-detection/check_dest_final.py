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
    # Check main tables
    tables = ['customers', 'employees', 'accounts', 'transactions']
    print("Destination database row counts:")
    for table in tables:
        result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.fetchone()[0]
        print(f"  {table}: {count}")

    # Check FK integrity
    result = connection.execute(text("""
        SELECT COUNT(*)
        FROM transactions t
        LEFT JOIN accounts a ON t.account_id = a.account_id
        WHERE a.account_id IS NULL
    """))
    orphaned = result.fetchone()[0]
    print(f"\nOrphaned transactions: {orphaned}")

conn.disconnect()
