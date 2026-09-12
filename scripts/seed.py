import os
import sqlite3

os.makedirs("data", exist_ok=True)

conn = sqlite3.connect("data/example.db")

try:
    conn.execute("PRAGMA foreign_keys = ON;")

    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS orders;")
    cursor.execute("DROP TABLE IF EXISTS customers;")

    cursor.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            country TEXT,
            join_date TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            order_date TEXT,
            total_amount REAL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) 
                ON DELETE CASCADE ON UPDATE CASCADE
        );
    """)

    customers = [
        (1, "Alice Smith", "alice@example.com", "USA", "2024-01-15"),
        (2, "Bob Jones", "bob@example.com", "Canada", "2024-02-20"),
        (3, "Charlie Brown", "charlie@example.com", "USA", "2024-03-10"),
    ]

    orders = [
        (101, 1, "2026-08-01", 150.00, "Shipped"),
        (102, 1, "2026-09-05", 45.50, "Pending"),
        (103, 2, "2026-09-10", 200.00, "Shipped"),
        (104, 3, "2026-09-11", 89.99, "Cancelled"),
    ]

    with conn:
        cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers)
        cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders)

    print("Database created!")

except sqlite3.Error as e:
    print(f"Database Error: {e}")

finally:
    conn.close()
