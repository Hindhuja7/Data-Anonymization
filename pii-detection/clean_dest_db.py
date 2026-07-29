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
    # Drop all tables
    tables_to_drop = ['accounts', 'customers', 'employees', 'transactions']
    for table in tables_to_drop:
        try:
            connection.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
            print(f"Dropped {table}")
        except Exception as e:
            print(f"Error dropping {table}: {e}")

conn.disconnect()
print("Cleaned destination database")
