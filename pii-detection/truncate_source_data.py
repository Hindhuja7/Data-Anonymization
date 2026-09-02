"""
Script to keep only first 1000 rows from each table in source database.
This speeds up anonymization pipeline processing for testing.
"""

import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import text

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv("SOURCE_DB_HOST")
DB_PORT = os.getenv("SOURCE_DB_PORT")
DB_USERNAME = os.getenv("SOURCE_DB_USERNAME")
DB_PASSWORD = os.getenv("SOURCE_DB_PASSWORD")
DB_NAME = os.getenv("SOURCE_DB_NAME")
DB_TYPE = os.getenv("SOURCE_DB_TYPE", "postgresql")

# Create database connection string
if DB_TYPE == "postgresql":
    DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    raise ValueError(f"Unsupported database type: {DB_TYPE}")

# Create engine
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL)

print("Connecting to source database...")
print(f"Host: {DB_HOST}")
print(f"Database: {DB_NAME}")
print()

# Tables in processing order (child tables first for FK safety)
tables = [
    "transactions",  # Child table
    "accounts",      # Child table  
    "customers",     # Parent table
    "employees"      # Parent table
]

ROWS_TO_KEEP = 1000

try:
    with engine.begin() as conn:
        # Step 1: Drop foreign key constraints
        print("Step 1: Dropping foreign key constraints...")
        conn.execute(text('ALTER TABLE "transactions" DROP CONSTRAINT IF EXISTS transactions_account_id_fkey'))
        conn.execute(text('ALTER TABLE "accounts" DROP CONSTRAINT IF EXISTS accounts_customer_id_fkey'))
        print("  ✓ Dropped foreign key constraints")
        
        # Step 2: Truncate parent tables first (customers, employees)
        print("\nStep 2: Truncating parent tables...")
        
        for table in ["customers", "employees"]:
            print(f"  Processing {table}...")
            current_count = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
            print(f"    Current rows: {current_count}")
            
            if current_count > ROWS_TO_KEEP:
                pk_query = f'''
                    SELECT a.attname
                    FROM pg_index i
                    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                    WHERE i.indrelid = '{table}'::regclass AND i.indisprimary
                '''
                pk_result = conn.execute(text(pk_query)).fetchone()
                
                if pk_result:
                    pk_column = pk_result[0]
                    delete_query = f'''
                        DELETE FROM "{table}"
                        WHERE "{pk_column}" NOT IN (
                            SELECT "{pk_column}"
                            FROM "{table}"
                            ORDER BY "{pk_column}"
                            LIMIT {ROWS_TO_KEEP}
                        )
                    '''
                    result = conn.execute(text(delete_query))
                    new_count = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
                    print(f"    Deleted: {result.rowcount} rows, Remaining: {new_count}")
        
        # Step 3: Truncate accounts to only keep those referencing kept customers
        print("\nStep 3: Truncating accounts (referencing kept customers)...")
        
        # Get customer IDs to keep
        customers_to_keep = conn.execute(text(f'''
            SELECT customer_id FROM "customers" 
            ORDER BY customer_id LIMIT {ROWS_TO_KEEP}
        ''')).fetchall()
        customer_ids = [row[0] for row in customers_to_keep]
        
        if customer_ids:
            delete_accounts = f'''
                DELETE FROM "accounts"
                WHERE customer_id NOT IN ({','.join(map(str, customer_ids))})
            '''
            result = conn.execute(text(delete_accounts))
            acc_count = conn.execute(text('SELECT COUNT(*) FROM "accounts"')).scalar()
            print(f"  Deleted {result.rowcount} accounts, Remaining: {acc_count}")
            
            # If still more than 1000 accounts, truncate further
            if acc_count > ROWS_TO_KEEP:
                delete_excess_acc = f'''
                    DELETE FROM "accounts"
                    WHERE account_id NOT IN (
                        SELECT account_id FROM "accounts" 
                        ORDER BY account_id LIMIT {ROWS_TO_KEEP}
                    )
                '''
                result = conn.execute(text(delete_excess_acc))
                acc_count = conn.execute(text('SELECT COUNT(*) FROM "accounts"')).scalar()
                print(f"  Further deleted {result.rowcount} accounts, Remaining: {acc_count}")
        
        # Step 4: Truncate transactions to only keep those referencing kept accounts
        print("\nStep 4: Truncating transactions (referencing kept accounts)...")
        
        # Get account IDs to keep
        accounts_to_keep = conn.execute(text(f'''
            SELECT account_id FROM "accounts" 
            ORDER BY account_id LIMIT {ROWS_TO_KEEP}
        ''')).fetchall()
        account_ids = [row[0] for row in accounts_to_keep]
        
        if account_ids:
            delete_trans = f'''
                DELETE FROM "transactions"
                WHERE account_id NOT IN ({','.join(map(str, account_ids))})
            '''
            result = conn.execute(text(delete_trans))
            trans_count = conn.execute(text('SELECT COUNT(*) FROM "transactions"')).scalar()
            print(f"  Deleted {result.rowcount} transactions, Remaining: {trans_count}")
            
            # If still more than 1000 transactions, truncate further
            if trans_count > ROWS_TO_KEEP:
                delete_excess_trans = f'''
                    DELETE FROM "transactions"
                    WHERE transaction_id NOT IN (
                        SELECT transaction_id FROM "transactions" 
                        ORDER BY transaction_id LIMIT {ROWS_TO_KEEP}
                    )
                '''
                result = conn.execute(text(delete_excess_trans))
                trans_count = conn.execute(text('SELECT COUNT(*) FROM "transactions"')).scalar()
                print(f"  Further deleted {result.rowcount} transactions, Remaining: {trans_count}")
        
        # Step 5: Recreate foreign key constraints
        print("\nStep 5: Recreating foreign key constraints...")
        
        conn.execute(text('''
            ALTER TABLE "accounts" 
            ADD CONSTRAINT accounts_customer_id_fkey 
            FOREIGN KEY (customer_id) REFERENCES "customers"(customer_id)
        '''))
        print("  ✓ Added accounts → customers FK")
        
        conn.execute(text('''
            ALTER TABLE "transactions" 
            ADD CONSTRAINT transactions_account_id_fkey 
            FOREIGN KEY (account_id) REFERENCES "accounts"(account_id)
        '''))
        print("  ✓ Added transactions → accounts FK")
    
    print("\n✓ Successfully truncated all tables to maintain referential integrity")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
