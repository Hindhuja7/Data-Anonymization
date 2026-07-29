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
    # Check for accounts with customer_id not in customers
    result = connection.execute(text("""
        SELECT a.customer_id, COUNT(*) as count
        FROM accounts a
        LEFT JOIN customers c ON a.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
        GROUP BY a.customer_id
        ORDER BY count DESC
        LIMIT 10
    """))

    print("Accounts with customer_id not in customers table (source):")
    for row in result:
        print(f"  customer_id {row[0]}: {row[1]} accounts")

    # Get total count
    result = connection.execute(text("""
        SELECT COUNT(*)
        FROM accounts a
        LEFT JOIN customers c ON a.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
    """))
    total = result.fetchone()[0]
    print(f"\nTotal orphaned accounts in source: {total}")

conn.disconnect()
