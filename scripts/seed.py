import os
import sqlite3

os.makedirs("data", exist_ok=True)

db_path = "data/example.db"
conn = sqlite3.connect(db_path)

try:
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # Drop existing tables in reverse order of foreign key dependency
    cursor.execute("DROP TABLE IF EXISTS reviews;")
    cursor.execute("DROP TABLE IF EXISTS order_items;")
    cursor.execute("DROP TABLE IF EXISTS orders;")
    cursor.execute("DROP TABLE IF EXISTS products;")
    cursor.execute("DROP TABLE IF EXISTS categories;")
    cursor.execute("DROP TABLE IF EXISTS customers;")

    # 1. Categories Table
    cursor.execute("""
        CREATE TABLE categories (
            category_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        );
    """)

    # 2. Products Table
    cursor.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
                ON DELETE RESTRICT ON UPDATE CASCADE
        );
    """)

    # 3. Customers Table
    cursor.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            country TEXT,
            join_date TEXT
        );
    """)

    # 4. Orders Table
    cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) 
                ON DELETE CASCADE ON UPDATE CASCADE
        );
    """)

    # 5. Order Items Table
    cursor.execute("""
        CREATE TABLE order_items (
            item_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            unit_price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
                ON DELETE RESTRICT ON UPDATE CASCADE
        );
    """)

    # 6. Reviews Table
    cursor.execute("""
        CREATE TABLE reviews (
            review_id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            comment TEXT,
            review_date TEXT,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                ON DELETE CASCADE ON UPDATE CASCADE
        );
    """)

    # --- Sample Data ---

    categories = [
        (1, "Electronics", "Gadgets, computing, and electronic accessories"),
        (2, "Clothing", "Apparel, footwear, and fashion items"),
        (3, "Home & Kitchen", "Cookware, furniture, and home appliances"),
        (4, "Books", "Physical books, e-books, and magazines"),
        (5, "Sports & Outdoors", "Sporting gear, fitness equipment, and outdoor apparel"),
    ]

    products = [
        (1, 1, "Wireless Noise-Canceling Headphones", 199.99, 45),
        (2, 1, "Mechanical Gaming Keyboard", 89.99, 60),
        (3, 1, "USB-C Portable Monitor 15.6 inch", 149.50, 25),
        (4, 2, "Organic Cotton T-Shirt", 24.99, 120),
        (5, 2, "Waterproof Running Shoes", 110.00, 35),
        (6, 3, "Stainless Steel Pour-Over Coffee Maker", 34.50, 50),
        (7, 3, "Cast Iron Skillet 12 inch", 45.00, 30),
        (8, 4, "Designing Data-Intensive Applications", 42.00, 80),
        (9, 4, "Clean Code by Robert C. Martin", 38.50, 40),
        (10, 5, "Yoga Mat with Alignment Lines", 28.00, 75),
    ]

    customers = [
        (1, "Alice Smith", "alice@example.com", "USA", "2024-01-15"),
        (2, "Bob Jones", "bob@example.com", "Canada", "2024-02-20"),
        (3, "Charlie Brown", "charlie@example.com", "USA", "2024-03-10"),
        (4, "Diana Prince", "diana@example.com", "UK", "2024-04-05"),
        (5, "Ethan Hunt", "ethan@example.com", "Germany", "2024-05-12"),
        (6, "Fiona Gallagher", "fiona@example.com", "USA", "2024-06-18"),
        (7, "George Clark", "george@example.com", "Canada", "2024-07-22"),
        (8, "Hannah Abbott", "hannah@example.com", "UK", "2024-08-30"),
    ]

    orders = [
        (101, 1, "2026-08-01", 150.00, "Shipped"),
        (102, 1, "2026-09-05", 45.50, "Pending"),
        (103, 2, "2026-09-10", 200.00, "Shipped"),
        (104, 3, "2026-09-11", 89.99, "Cancelled"),
        (105, 4, "2026-09-12", 244.99, "Shipped"),
        (106, 5, "2026-09-12", 69.00, "Delivered"),
        (107, 6, "2026-09-13", 199.99, "Pending"),
        (108, 2, "2026-09-13", 80.50, "Shipped"),
    ]

    order_items = [
        (1, 101, 2, 1, 89.99),
        (2, 101, 6, 1, 34.50),
        (3, 102, 7, 1, 45.00),
        (4, 103, 1, 1, 199.99),
        (5, 104, 2, 1, 89.99),
        (6, 105, 1, 1, 199.99),
        (7, 105, 4, 1, 24.99),
        (8, 106, 6, 2, 34.50),
        (9, 107, 1, 1, 199.99),
        (10, 108, 8, 1, 42.00),
        (11, 108, 9, 1, 38.50),
    ]

    reviews = [
        (1, 1, 1, 5, "Best noise-canceling headphones I have used!", "2026-08-10"),
        (2, 1, 4, 4, "Great audio quality, slightly heavy on the head.", "2026-09-14"),
        (3, 2, 1, 5, "Tactile switches feel fantastic for typing.", "2026-08-15"),
        (4, 6, 5, 5, "Makes smooth pour-over coffee every morning.", "2026-09-14"),
        (5, 7, 1, 4, "Sturdy skillet, seasoned well.", "2026-09-08"),
        (6, 8, 2, 5, "A must-read for distributed systems engineers.", "2026-09-15"),
        (7, 4, 4, 3, "Good shirt but shrank slightly after wash.", "2026-09-15"),
    ]

    with conn:
        cursor.executemany("INSERT INTO categories VALUES (?, ?, ?)", categories)
        cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", products)
        cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers)
        cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders)
        cursor.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?)", order_items)
        cursor.executemany("INSERT INTO reviews VALUES (?, ?, ?, ?, ?, ?)", reviews)

    print(f"Database successfully created at '{db_path}' with 6 tables!")

except sqlite3.Error as e:
    print(f"Database Error: {e}")
    raise

finally:
    conn.close()
