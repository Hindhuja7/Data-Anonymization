"""
Create a simple test SQLite database for 17-step pipeline testing
"""

import sqlite3
import os

def create_test_database():
    """Create a small test database with sample data"""
    db_path = "test_source.db"
    
    # Remove existing test database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables with PK/FK relationships
    cursor.execute("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            address TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            order_date TEXT,
            amount REAL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)
    
    # Insert sample data
    customers_data = [
        (1, "John Doe", "john.doe@email.com", "+91-9876543210", "123 Main St, Mumbai"),
        (2, "Jane Smith", "jane.smith@email.com", "+91-9876543211", "456 Oak Ave, Delhi"),
        (3, "Bob Johnson", "bob.johnson@email.com", "+91-9876543212", "789 Pine Rd, Bangalore"),
        (4, "Alice Williams", "alice.williams@email.com", "+91-9876543213", "321 Elm St, Chennai"),
        (5, "Charlie Brown", "charlie.brown@email.com", "+91-9876543214", "654 Maple Dr, Hyderabad"),
    ]
    
    cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers_data)
    
    orders_data = [
        (1, 1, "2024-01-15", 1500.00),
        (2, 1, "2024-02-20", 2500.00),
        (3, 2, "2024-01-18", 1800.00),
        (4, 3, "2024-03-10", 3200.00),
        (5, 4, "2024-02-25", 2100.00),
    ]
    
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", orders_data)
    
    order_items_data = [
        (1, 1, "Laptop", 1, 45000.00),
        (2, 1, "Mouse", 2, 500.00),
        (3, 2, "Keyboard", 1, 1500.00),
        (4, 3, "Monitor", 1, 12000.00),
        (5, 4, "Headphones", 1, 3000.00),
        (6, 5, "Webcam", 1, 2500.00),
    ]
    
    cursor.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?)", order_items_data)
    
    conn.commit()
    conn.close()
    
    print(f"✓ Test database created: {db_path}")
    print(f"  - 5 customers")
    print(f"  - 5 orders")
    print(f"  - 6 order items")
    print(f"  - PK/FK relationships established")
    
    return db_path

if __name__ == "__main__":
    create_test_database()
