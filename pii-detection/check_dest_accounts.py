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

# Check specific account_ids from error messages
problem_account_ids = [49012, 34217, 39579]

with engine.connect() as connection:
    print("Checking if problem account_ids exist in destination accounts table:")
    for acc_id in problem_account_ids:
        result = connection.execute(text(f"SELECT account_id FROM accounts WHERE account_id = {acc_id}"))
        row = result.fetchone()
        if row:
            print(f"  account_id {acc_id}: EXISTS")
        else:
            print(f"  account_id {acc_id}: NOT FOUND")

    # Check total accounts in destination
    result = connection.execute(text("SELECT COUNT(*) FROM accounts"))
    total = result.fetchone()[0]
    print(f"\nTotal accounts in destination: {total}")

    # Check total accounts in source
    conn2 = DatabaseConnector(
        database_type=os.getenv('SOURCE_DB_TYPE'),
        host=os.getenv('SOURCE_DB_HOST'),
        port=int(os.getenv('SOURCE_DB_PORT')),
        username=os.getenv('SOURCE_DB_USERNAME'),
        password=os.getenv('SOURCE_DB_PASSWORD'),
        database_name=os.getenv('SOURCE_DB_NAME')
    )
    engine2 = conn2.connect()
    with engine2.connect() as connection2:
        result = connection2.execute(text("SELECT COUNT(*) FROM accounts"))
        total_source = result.fetchone()[0]
        print(f"Total accounts in source: {total_source}")
    conn2.disconnect()

conn.disconnect()
