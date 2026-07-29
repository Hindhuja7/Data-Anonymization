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

# Check specific account_ids from error messages
problem_account_ids = [49012, 34217, 39579]

with engine.connect() as connection:
    print("Checking if problem account_ids exist in accounts table:")
    for acc_id in problem_account_ids:
        result = connection.execute(text(f"SELECT account_id FROM accounts WHERE account_id = {acc_id}"))
        row = result.fetchone()
        if row:
            print(f"  account_id {acc_id}: EXISTS")
        else:
            print(f"  account_id {acc_id}: NOT FOUND")

    # Check if these account_ids exist in transactions
    print("\nChecking if problem account_ids exist in transactions table:")
    for acc_id in problem_account_ids:
        result = connection.execute(text(f"SELECT COUNT(*) FROM transactions WHERE account_id = {acc_id}"))
        count = result.fetchone()[0]
        print(f"  account_id {acc_id}: {count} transactions reference it")

conn.disconnect()
