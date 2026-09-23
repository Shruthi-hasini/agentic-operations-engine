import sqlite3

def init_sql_db():
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    
    # Create Orders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT,
        item_name TEXT,
        amount REAL,
        status TEXT,
        delivery_date TEXT
    )
    """)
    
    # Seed Mock Data
    sample_orders = [
        ("ORD1001", "CUST01", "Wireless Headphones", 89.99, "Delivered", "2026-03-01"),
        ("ORD1002", "CUST02", "Mechanical Keyboard", 120.00, "Delivered", "2026-03-10"),
        ("ORD1003", "CUST01", "USB-C Hub", 35.50, "In Transit", "2026-03-24")
    ]
    
    cursor.executemany("INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?, ?, ?)", sample_orders)
    conn.commit()
    conn.close()
    print("✅ SQL Database (orders.db) successfully created with sample orders!")

if __name__ == "__main__":
    init_sql_db()