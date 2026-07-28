"""
Test PostgreSQL database connections using .env credentials
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def test_postgres_connection(db_type, host, port, username, password, database_name, sslmode):
    """Test PostgreSQL database connection"""
    try:
        if sslmode:
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database_name}?sslmode={sslmode}"
        else:
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database_name}"
        
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            
        print(f"✓ {db_type} PostgreSQL connection successful")
        print(f"  Host: {host}:{port}")
        print(f"  Database: {database_name}")
        print(f"  Version: {version[:50]}...")
        
        # Get table count
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = result.fetchone()[0]
        
        print(f"  Tables in public schema: {table_count}")
        
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"✗ {db_type} PostgreSQL connection failed: {e}")
        return False

def main():
    print("="*60)
    print("POSTGRESQL CONNECTION TEST")
    print("="*60)
    
    # Source database
    source_host = os.getenv("SOURCE_DB_HOST")
    source_port = os.getenv("SOURCE_DB_PORT")
    source_username = os.getenv("SOURCE_DB_USERNAME")
    source_password = os.getenv("SOURCE_DB_PASSWORD")
    source_database = os.getenv("SOURCE_DB_NAME")
    source_sslmode = os.getenv("SOURCE_DB_SSLMODE")
    
    # Destination database
    dest_host = os.getenv("DEST_DB_HOST")
    dest_port = os.getenv("DEST_DB_PORT")
    dest_username = os.getenv("DEST_DB_USERNAME")
    dest_password = os.getenv("DEST_DB_PASSWORD")
    dest_database = os.getenv("DEST_DB_NAME")
    dest_sslmode = os.getenv("DEST_DB_SSLMODE")
    
    print("\nSource Database Configuration:")
    print(f"  Type: PostgreSQL")
    print(f"  Host: {source_host}:{source_port}")
    print(f"  Database: {source_database}")
    print(f"  SSL: {source_sslmode}")
    
    print("\nDestination Database Configuration:")
    print(f"  Type: PostgreSQL")
    print(f"  Host: {dest_host}:{dest_port}")
    print(f"  Database: {dest_database}")
    print(f"  SSL: {dest_sslmode}")
    
    # Verify source != destination
    if source_database == dest_database:
        print("\n⚠ WARNING: Source and destination databases are the same!")
        print("  This is not safe for production use.")
    else:
        print("\n✓ Source and destination databases are different")
    
    print("\n" + "="*60)
    print("Testing Connections")
    print("="*60)
    
    source_ok = test_postgres_connection(
        "SOURCE", source_host, source_port, source_username, 
        source_password, source_database, source_sslmode
    )
    
    dest_ok = test_postgres_connection(
        "DESTINATION", dest_host, dest_port, dest_username, 
        dest_password, dest_database, dest_sslmode
    )
    
    print("\n" + "="*60)
    print("CONNECTION TEST SUMMARY")
    print("="*60)
    print(f"Source PostgreSQL: {'PASS' if source_ok else 'FAIL'}")
    print(f"Destination PostgreSQL: {'PASS' if dest_ok else 'FAIL'}")
    
    if source_ok and dest_ok:
        print("\n✓ Both database connections successful")
        return 0
    else:
        print("\n✗ One or more database connections failed")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
