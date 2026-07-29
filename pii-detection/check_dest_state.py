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
    # Check all tables
    tables = ['customers', 'employees', 'accounts', 'transactions']
    print("Destination database row counts:")
    for table in tables:
        result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.fetchone()[0]
        print(f"  {table}: {count}")

    # Check if accounts table exists and has structure
    print("\nAccounts table structure:")
    result = connection.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'accounts'
        ORDER BY ordinal_position
    """))
    for row in result:
        print(f"  {row[0]}: {row[1]}")

conn.disconnect()
