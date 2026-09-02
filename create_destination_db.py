"""
Create the destination PostgreSQL database for testing
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def create_destination_database():
    """Create the destination database if it doesn't exist"""
    try:
        # Connect to the default postgres database to create a new database
        dest_host = os.getenv("DEST_DB_HOST")
        dest_port = os.getenv("DEST_DB_PORT")
        dest_username = os.getenv("DEST_DB_USERNAME")
        dest_password = os.getenv("DEST_DB_PASSWORD")
        dest_database = os.getenv("DEST_DB_NAME")
        dest_sslmode = os.getenv("DEST_DB_SSLMODE")
        
        # Connect to postgres database first to create the new database
        if dest_sslmode:
            connection_string = f"postgresql://{dest_username}:{dest_password}@{dest_host}:{dest_port}/postgres?sslmode={dest_sslmode}"
        else:
            connection_string = f"postgresql://{dest_username}:{dest_password}@{dest_host}:{dest_port}/postgres"
        
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{dest_database}'"))
            exists = result.fetchone()
            
            if exists:
                print(f"✓ Destination database '{dest_database}' already exists")
            else:
                # Create the database
                conn.execute(text(f"COMMIT"))  # Commit any existing transaction
                conn.execute(text(f"CREATE DATABASE {dest_database}"))
                print(f"✓ Created destination database '{dest_database}'")
        
        engine.dispose()
        
        # Verify connection to the new database
        if dest_sslmode:
            connection_string = f"postgresql://{dest_username}:{dest_password}@{dest_host}:{dest_port}/{dest_database}?sslmode={dest_sslmode}"
        else:
            connection_string = f"postgresql://{dest_username}:{dest_password}@{dest_host}:{dest_port}/{dest_database}"
        
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
        
        print(f"✓ Verified connection to '{dest_database}'")
        print(f"  Version: {version[:50]}...")
        
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"✗ Failed to create destination database: {e}")
        return False

if __name__ == "__main__":
    import sys
    sys.exit(0 if create_destination_database() else 1)
