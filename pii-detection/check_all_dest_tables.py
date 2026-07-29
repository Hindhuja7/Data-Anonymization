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
    # List all tables
    result = connection.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """))
    
    print("Tables in destination database:")
    tables = []
    for row in result:
        tables.append(row[0])
        print(f"  {row[0]}")
    
    # Check row counts
    print("\nRow counts:")
    for table in tables:
        result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.fetchone()[0]
        print(f"  {table}: {count}")

conn.disconnect()
