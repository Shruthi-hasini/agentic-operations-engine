import sqlite3

def init_db():
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    
    # Drop table if exists to reset schema cleanly
    cursor.execute("DROP TABLE IF EXISTS orders")
    
    # Create orders table with price column
    cursor.execute("""
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            item TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)
    
    # Insert test order records
    test_orders = [
        ("ORD1001", "Alice Smith", "Wireless Headphones", 29.99, "DELIVERED"),
        ("ORD1002", "Bob Jones", "4K Gaming Monitor", 120.00, "DELIVERED"),
        ("ORD1003", "Charlie Brown", "USB-C Cable", 15.00, "SHIPPED")
    ]
    
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", test_orders)
    
    conn.commit()
    conn.close()
    print("Database re-initialized successfully with 'price' column!")

if __name__ == "__main__":
    init_db()