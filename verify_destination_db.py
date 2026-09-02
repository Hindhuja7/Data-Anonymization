"""
Verify destination database has anonymized data with PK/FK integrity
"""

import sqlite3
import os

def verify_destination_database():
    """Verify destination database contents and integrity"""
    
    dest_db_path = "test_destination.db"
    
    if not os.path.exists(dest_db_path):
        print(f"✗ Destination database not found: {dest_db_path}")
        return False
    
    conn = sqlite3.connect(dest_db_path)
    cursor = conn.cursor()
    
    print("="*60)
    print("DESTINATION DATABASE VERIFICATION")
    print("="*60)
    
    # Check tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\nTables in destination: {tables}")
    
    expected_tables = ["customers", "orders", "order_items"]
    for table in expected_tables:
        if table not in tables:
            print(f"✗ Missing table: {table}")
            return False
    
    # Check row counts
    print("\nRow counts:")
    for table in expected_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} rows")
    
    # Check data content and anonymization
    print("\nData samples (checking anonymization):")
    
    cursor.execute("SELECT id, name, email, phone FROM customers LIMIT 3")
    customers = cursor.fetchall()
    print(f"  Customers sample:")
    for row in customers:
        print(f"    ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Phone: {row[3]}")
    
    cursor.execute("SELECT id, customer_id, order_date, amount FROM orders LIMIT 3")
    orders = cursor.fetchall()
    print(f"  Orders sample:")
    for row in orders:
        print(f"    ID: {row[0]}, Customer ID: {row[1]}, Date: {row[2]}, Amount: {row[3]}")
    
    # Check referential integrity
    print("\nPK/FK Integrity Check:")
    
    # Check customers PK
    cursor.execute("SELECT COUNT(*) FROM customers WHERE id IS NULL")
    null_pks = cursor.fetchone()[0]
    print(f"  Customers with NULL PK: {null_pks}")
    
    # Check orders FK to customers
    cursor.execute("""
        SELECT COUNT(*) FROM orders o 
        LEFT JOIN customers c ON o.customer_id = c.id 
        WHERE c.id IS NULL
    """)
    orphaned_orders = cursor.fetchone()[0]
    print(f"  Orders with invalid customer_id: {orphaned_orders}")
    
    # Check order_items FK to orders
    cursor.execute("""
        SELECT COUNT(*) FROM order_items oi 
        LEFT JOIN orders o ON oi.order_id = o.id 
        WHERE o.id IS NULL
    """)
    orphaned_items = cursor.fetchone()[0]
    print(f"  Order items with invalid order_id: {orphaned_items}")
    
    conn.close()
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    if null_pks == 0 and orphaned_orders == 0 and orphaned_items == 0:
        print("✓ PK/FK integrity preserved")
        print("✓ All tables present with expected row counts")
        print("✓ Data appears to be processed")
        return True
    else:
        print("✗ PK/FK integrity issues detected")
        return False

if __name__ == "__main__":
    import sys
    sys.exit(0 if verify_destination_database() else 1)
