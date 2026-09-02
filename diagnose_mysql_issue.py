"""
Diagnostic script to investigate MySQL read-only error during CRM dataset generation.
This script will check connection settings, permissions, and test INSERT operations.
"""

import os
import pymysql
from dotenv import load_dotenv
import ssl

# Load environment variables
load_dotenv()

def get_connection():
    """Create MySQL connection using environment variables"""
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        user=os.getenv('MYSQL_USERNAME'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE'),
        ssl={'ssl_ca': os.getenv('MYSQL_SSL_CA')} if os.getenv('MYSQL_SSL_CA') else None
    )

def run_diagnostics():
    """Run comprehensive diagnostics"""
    print("=" * 80)
    print("MYSQL DIAGNOSTIC REPORT")
    print("=" * 80)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Connection details
        print("\n1. CONNECTION DETAILS")
        print("-" * 80)
        print(f"Host: {os.getenv('MYSQL_HOST')}")
        print(f"Port: {os.getenv('MYSQL_PORT')}")
        print(f"Database: {os.getenv('MYSQL_DATABASE')}")
        print(f"User: {os.getenv('MYSQL_USERNAME')}")
        
        cursor.execute("SELECT CONNECTION_ID(), @@hostname, @@port")
        conn_id, hostname, port = cursor.fetchone()
        print(f"Connection ID: {conn_id}")
        print(f"MySQL Hostname: {hostname}")
        print(f"MySQL Port: {port}")
        
        # 2. Check if primary or replica
        print("\n2. PRIMARY VS REPLICA CHECK")
        print("-" * 80)
        cursor.execute("SELECT @@read_only, @@super_read_only")
        read_only, super_read_only = cursor.fetchone()
        print(f"@@read_only: {read_only}")
        print(f"@@super_read_only: {super_read_only}")
        
        cursor.execute("SHOW VARIABLES LIKE 'server_id'")
        server_id = cursor.fetchone()
        print(f"Server ID: {server_id[1] if server_id else 'N/A'}")
        
        # 3. Current user and grants
        print("\n3. USER AND GRANTS")
        print("-" * 80)
        cursor.execute("SELECT CURRENT_USER(), USER()")
        current_user, user = cursor.fetchone()
        print(f"CURRENT_USER(): {current_user}")
        print(f"USER(): {user}")
        
        cursor.execute("SHOW GRANTS FOR CURRENT_USER()")
        grants = cursor.fetchall()
        print("\nGrants:")
        for grant in grants:
            print(f"  {grant[0]}")
        
        # 4. Actual row counts
        print("\n4. ACTUAL ROW COUNTS IN CRM TABLES")
        print("-" * 80)
        tables = [
            'companies', 'customers', 'contacts', 'sales_representatives',
            'leads', 'opportunities', 'contracts', 'support_tickets',
            'activities', 'invoices'
        ]
        
        total_rows = 0
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_rows += count
                print(f"  {table:25} {count:>12,} rows")
            except Exception as e:
                print(f"  {table:25} ERROR: {e}")
        
        print(f"\n  Total: {total_rows:>12,} rows")
        
        # 5. Test INSERT with temporary table
        print("\n5. TEST INSERT WITH TEMPORARY TABLE")
        print("-" * 80)
        try:
            cursor.execute("CREATE TEMPORARY TABLE test_insert (id INT PRIMARY KEY, value VARCHAR(50))")
            print("✓ Created temporary table test_insert")
            
            cursor.execute("INSERT INTO test_insert VALUES (1, 'test')")
            conn.commit()
            print("✓ Successfully inserted test row")
            
            cursor.execute("SELECT COUNT(*) FROM test_insert")
            count = cursor.fetchone()[0]
            print(f"✓ Temporary table has {count} row(s)")
            
            cursor.execute("DROP TEMPORARY TABLE test_insert")
            print("✓ Dropped temporary table")
            
        except Exception as e:
            print(f"✗ INSERT test failed: {e}")
            conn.rollback()
        
        # 6. Test INSERT on actual CRM table (companies)
        print("\n6. TEST INSERT ON ACTUAL CRM TABLE (companies)")
        print("-" * 80)
        try:
            cursor.execute("""
                INSERT INTO companies (name, industry, website, phone, address, city, state, country, postal_code)
                VALUES ('Test Company', 'Technology', 'http://test.com', '+91-9876543210', '123 Test St', 'Test City', 'TS', 'India', '123456')
            """)
            conn.commit()
            print("✓ Successfully inserted test company")
            
            cursor.execute("SELECT COUNT(*) FROM companies WHERE name = 'Test Company'")
            count = cursor.fetchone()[0]
            print(f"✓ Found {count} test company row(s)")
            
            # Clean up
            cursor.execute("DELETE FROM companies WHERE name = 'Test Company'")
            conn.commit()
            print("✓ Cleaned up test company")
            
        except Exception as e:
            print(f"✗ INSERT on companies failed: {e}")
            conn.rollback()
        
        # 7. Check progress file
        print("\n7. PROGRESS FILE STATUS")
        print("-" * 80)
        progress_file = "crm_generation_progress.json"
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                import json
                progress = json.load(f)
            print(f"Progress file exists: {progress_file}")
            print(f"Last stage: {progress.get('last_stage', 'N/A')}")
            print(f"Completed tables: {list(progress.get('completed_tables', {}).keys())}")
        else:
            print("Progress file not found")
        
        # 8. Check for any recent errors or warnings
        print("\n8. RECENT ERRORS/WARNINGS")
        print("-" * 80)
        try:
            cursor.execute("SHOW WARNINGS")
            warnings = cursor.fetchall()
            if warnings:
                for warning in warnings:
                    print(f"  {warning}")
            else:
                print("  No warnings")
        except:
            print("  Could not retrieve warnings")
        
    finally:
        cursor.close()
        conn.close()
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_diagnostics()
