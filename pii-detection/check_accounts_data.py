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
    # Check if accounts table has any data
    result = connection.execute(text("SELECT COUNT(*) FROM accounts"))
    count = result.fetchone()[0]
    print(f"Destination accounts count: {count}")

    if count > 0:
        # Show sample data
        result = connection.execute(text("SELECT * FROM accounts LIMIT 5"))
        print("\nSample accounts data:")
        for row in result:
            print(f"  {row}")
    else:
        print("Accounts table is empty - this is why transactions FK fails")

conn.disconnect()
