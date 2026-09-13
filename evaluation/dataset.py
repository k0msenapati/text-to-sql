from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvalTestCase:
    id: str
    question: str
    ground_truth_sql: str
    difficulty: str  # "easy", "medium", "hard"
    category: str
    order_matters: bool = False
    expected_rows: list[dict[str, Any]] = field(default_factory=list)


BENCHMARK_CASES: list[EvalTestCase] = [
    # --- EASY ---
    EvalTestCase(
        id="EASY-01",
        question="List all customers who live in Canada.",
        ground_truth_sql="SELECT name FROM customers WHERE country = 'Canada';",
        difficulty="easy",
        category="Filtering",
        order_matters=False,
    ),
    EvalTestCase(
        id="EASY-02",
        question="How many total customers are in the database?",
        ground_truth_sql="SELECT COUNT(*) AS total FROM customers;",
        difficulty="easy",
        category="Aggregation",
        order_matters=False,
    ),
    EvalTestCase(
        id="EASY-03",
        question="Find the names and prices of all products that cost more than 100 dollars.",
        ground_truth_sql="SELECT name, price FROM products WHERE price > 100;",
        difficulty="easy",
        category="Filtering",
        order_matters=False,
    ),
    EvalTestCase(
        id="EASY-04",
        question="List all products with less than 30 items in stock. Show name and stock quantity.",
        ground_truth_sql="SELECT name, stock_quantity FROM products WHERE stock_quantity < 30;",
        difficulty="easy",
        category="Filtering",
        order_matters=False,
    ),
    # --- MEDIUM ---
    EvalTestCase(
        id="MED-01",
        question="What are the top 3 most expensive products? Return their name and price ordered from highest to lowest.",
        ground_truth_sql="SELECT name, price FROM products ORDER BY price DESC LIMIT 3;",
        difficulty="medium",
        category="Sorting & Limit",
        order_matters=True,
    ),
    EvalTestCase(
        id="MED-02",
        question="What is the total revenue from orders with a status of 'Shipped'?",
        ground_truth_sql="SELECT SUM(total_amount) AS total_revenue FROM orders WHERE status = 'Shipped';",
        difficulty="medium",
        category="Aggregation & Filter",
        order_matters=False,
    ),
    EvalTestCase(
        id="MED-03",
        question="Show each customer's name and their corresponding order ID.",
        ground_truth_sql="SELECT c.name, o.order_id FROM customers c JOIN orders o ON c.customer_id = o.customer_id;",
        difficulty="medium",
        category="Join",
        order_matters=False,
    ),
    EvalTestCase(
        id="MED-04",
        question="How many products belong to each category? Return the category name and product count.",
        ground_truth_sql="""
        SELECT c.name, COUNT(p.product_id) AS product_count 
        FROM categories c 
        JOIN products p ON c.category_id = p.category_id 
        GROUP BY c.category_id, c.name;
        """,
        difficulty="medium",
        category="Group By & Count",
        order_matters=False,
    ),
    EvalTestCase(
        id="MED-05",
        question="Which products have an average review rating of at least 4.5? Return the product name.",
        ground_truth_sql="""
        SELECT p.name 
        FROM products p 
        JOIN reviews r ON p.product_id = r.product_id 
        GROUP BY p.product_id, p.name 
        HAVING AVG(r.rating) >= 4.5;
        """,
        difficulty="medium",
        category="Having & Aggregation",
        order_matters=False,
    ),
    EvalTestCase(
        id="MED-06",
        question="List the order IDs and total amounts for all orders placed in September 2026.",
        ground_truth_sql="SELECT order_id, total_amount FROM orders WHERE order_date LIKE '2026-09%';",
        difficulty="medium",
        category="Date Filtering",
        order_matters=False,
    ),
    # --- HARD ---
    EvalTestCase(
        id="HARD-01",
        question="Which customers purchased 'Wireless Noise-Canceling Headphones'? Return distinct customer names.",
        ground_truth_sql="""
        SELECT DISTINCT c.name 
        FROM customers c 
        JOIN orders o ON c.customer_id = o.customer_id 
        JOIN order_items oi ON o.order_id = oi.order_id 
        JOIN products p ON oi.product_id = p.product_id 
        WHERE p.name LIKE '%Noise-Canceling Headphones%';
        """,
        difficulty="hard",
        category="Multi-Table Join",
        order_matters=False,
    ),
    EvalTestCase(
        id="HARD-02",
        question="List each customer's name along with the number of orders they have placed, including customers who have zero orders.",
        ground_truth_sql="""
        SELECT c.name, COUNT(o.order_id) AS order_count 
        FROM customers c 
        LEFT JOIN orders o ON c.customer_id = o.customer_id 
        GROUP BY c.customer_id, c.name;
        """,
        difficulty="hard",
        category="Outer Join",
        order_matters=False,
    ),
    EvalTestCase(
        id="HARD-03",
        question="Find the customer who placed the single highest value order. Return the customer name and total amount.",
        ground_truth_sql="""
        SELECT c.name, o.total_amount 
        FROM customers c 
        JOIN orders o ON c.customer_id = o.customer_id 
        ORDER BY o.total_amount DESC 
        LIMIT 1;
        """,
        difficulty="hard",
        category="Ranking & Join",
        order_matters=True,
    ),
    EvalTestCase(
        id="HARD-04",
        question="What percentage of total orders have a status of 'Shipped'? Round to two decimal places.",
        ground_truth_sql="""
        SELECT ROUND((COUNT(CASE WHEN status = 'Shipped' THEN 1 END) * 100.0) / COUNT(*), 2) AS shipped_percentage 
        FROM orders;
        """,
        difficulty="hard",
        category="Calculated Metrics",
        order_matters=False,
    ),
    EvalTestCase(
        id="HARD-05",
        question="For customers who placed more than one order, what is their average order amount? Return customer name and average order amount.",
        ground_truth_sql="""
        SELECT c.name, ROUND(AVG(o.total_amount), 2) AS avg_order_val 
        FROM customers c 
        JOIN orders o ON c.customer_id = o.customer_id 
        GROUP BY c.customer_id, c.name 
        HAVING COUNT(o.order_id) > 1;
        """,
        difficulty="hard",
        category="Group By & Having",
        order_matters=False,
    ),
    # --- CHALLENGE / RUNTIME ERROR DIAGNOSTIC ---
    EvalTestCase(
        id="CHALLENGE-01",
        question="Extract the field key from malformed json payload {malformed_data} using json_extract.",
        ground_truth_sql="SELECT NULL;",
        difficulty="challenge",
        category="Runtime Execution Error Handling",
        order_matters=False,
    ),
]

