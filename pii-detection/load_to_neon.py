"""
Load test data into Neon PostgreSQL database.

This script:
1. Connects to Neon PostgreSQL database using environment variables
2. Creates tables using schema.sql
3. Loads CSV files (customers, employees, accounts, transactions)
4. Verifies row counts after import

Required environment variables:
- NEON_HOST: Neon database host (e.g., ep-xxx.region.aws.neon.tech)
- NEON_DATABASE: Database name (usually 'neondb')
- NEON_USER: Database username
- NEON_PASSWORD: Database password
- NEON_PORT: Database port (usually 5432)
"""

import os
import pandas as pd
import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine
from dotenv import load_dotenv
import traceback
import sys

# Load environment variables from .env file
load_dotenv()

# Configuration
OUTPUT_DIR = "test_data"
SCHEMA_FILE = f"{OUTPUT_DIR}/schema.sql"

# CSV files to load
CSV_FILES = {
    "customers": f"{OUTPUT_DIR}/customers.csv",
    "employees": f"{OUTPUT_DIR}/employees.csv",
    "accounts": f"{OUTPUT_DIR}/accounts.csv",
    "transactions": f"{OUTPUT_DIR}/transactions.csv"
}


def get_connection_params():
    """Get database connection parameters from environment variables."""
    return {
        "host": os.getenv("NEON_HOST"),
        "database": os.getenv("NEON_DATABASE", "neondb"),
        "user": os.getenv("NEON_USER"),
        "password": os.getenv("NEON_PASSWORD"),
        "port": os.getenv("NEON_PORT", "5432")
    }


def get_database_url():
    """Construct SQLAlchemy database URL from environment variables."""
    params = get_connection_params()
    return f"postgresql://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"


def print_table_schema(conn, table_name):
    """Print the schema of a table from PostgreSQL."""
    print(f"\nSchema for table '{table_name}':")
    cursor = conn.cursor()
    try:
        query = """
            SELECT column_name, data_type, character_maximum_length, numeric_precision, numeric_scale
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """
        cursor.execute(query, (table_name,))
        rows = cursor.fetchall()
        print(f"{'Column':<20} {'Type':<20} {'Max Len':<10} {'Precision':<10} {'Scale':<10}")
        print("-" * 70)
        for row in rows:
            col_name, data_type, max_len, precision, scale = row
            print(f"{col_name:<20} {data_type:<20} {str(max_len):<10} {str(precision):<10} {str(scale):<10}")
    except Exception as e:
        print(f"Error getting schema for {table_name}: {e}")
    finally:
        cursor.close()


def execute_schema(conn):
    """Execute schema.sql to create tables."""
    print("Executing schema.sql...")
    
    if not os.path.exists(SCHEMA_FILE):
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_FILE}")
    
    with open(SCHEMA_FILE, 'r') as f:
        schema_sql = f.read()
    
    cursor = conn.cursor()
    try:
        cursor.execute(schema_sql)
        conn.commit()
        print("Schema executed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error executing schema: {e}")
        raise
    finally:
        cursor.close()


def load_csv_to_table(table_name, csv_path, engine, conn):
    """Load CSV file into PostgreSQL table using COPY command."""
    print(f"Loading {csv_path} into {table_name} table...")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Print table schema for comparison
    print_table_schema(conn, table_name)
    
    # Use PostgreSQL COPY command for efficient bulk loading
    cursor = conn.cursor()
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            cursor.copy_expert(f"COPY {table_name} FROM STDIN WITH CSV HEADER NULL ''", f)
        conn.commit()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"Loaded {count} rows into {table_name}.")
        cursor.close()
        return count
    except Exception as e:
        conn.rollback()
        print(f"\nError loading {table_name}: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        cursor.close()
        raise


def verify_row_counts(conn):
    """Verify row counts in all tables."""
    print("\nVerifying row counts...")
    
    tables = ['customers', 'employees', 'accounts', 'transactions']
    cursor = conn.cursor()
    
    for table in tables:
        try:
            cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
            count = cursor.fetchone()[0]
            print(f"{table}: {count:,} rows")
        except Exception as e:
            print(f"Error counting rows in {table}: {e}")
    
    cursor.close()


def main():
    """Main function to load data into Neon PostgreSQL."""
    print("=" * 70)
    print("Loading Test Data into Neon PostgreSQL")
    print("=" * 70)
    
    # Validate environment variables
    required_vars = ['NEON_HOST', 'NEON_USER', 'NEON_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following environment variables in your .env file:")
        print("- NEON_HOST: Neon database host")
        print("- NEON_USER: Database username")
        print("- NEON_PASSWORD: Database password")
        print("\nOptional variables:")
        print("- NEON_DATABASE: Database name (default: neondb)")
        print("- NEON_PORT: Database port (default: 5432)")
        return
    
    try:
        # Connect to database using psycopg2 for schema execution
        params = get_connection_params()
        print(f"\nConnecting to PostgreSQL at {params['host']}...")
        
        conn = psycopg2.connect(**params)
        conn.autocommit = False
        
        # Execute schema
        execute_schema(conn)
        
        # Create SQLAlchemy engine for pandas.to_sql
        print("\nCreating SQLAlchemy engine...")
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        # Load CSV files (keep connection open for schema inspection)
        total_rows = 0
        for table_name, csv_path in CSV_FILES.items():
            rows = load_csv_to_table(table_name, csv_path, engine, conn)
            total_rows += rows
        
        # Close psycopg2 connection
        conn.close()
        
        print(f"\nTotal rows loaded: {total_rows:,}")
        
        # Verify row counts
        conn = psycopg2.connect(**params)
        verify_row_counts(conn)
        conn.close()
        
        print("\n" + "=" * 70)
        print("Data loading completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nError during data loading: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        raise
    finally:
        if 'engine' in locals():
            engine.dispose()


if __name__ == "__main__":
    main()
