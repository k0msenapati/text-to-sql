import ast


def test_agent_sql_select_columns(run_agent):
    """Test agent handles basic SELECT projection of specific columns."""
    question = "List all customer names and their email addresses."
    sql = "SELECT name, email FROM customers;"
    expected_answer = "Here are the customer names and emails: Alice, Bob, and Charlie."

    result = run_agent(question=question, generated_sql=sql, final_answer=expected_answer)

    assert result["is_valid"] is True
    assert result["validation_error"] is None
    assert "SELECT name, email FROM customers;" in result["sql_query"]
    assert result["answer"] == expected_answer

    rows = ast.literal_eval(result["sql_output"])
    assert len(rows) >= 3
    assert "name" in rows[0]
    assert "email" in rows[0]
    assert "country" not in rows[0]


def test_agent_sql_where_filtering(run_agent):
    """Test agent handles WHERE clause filtering."""
    question = "Show customers from the USA."
    sql = "SELECT customer_id, name, country FROM customers WHERE country = 'USA';"
    expected_answer = "Found 2 customers from USA: Alice Smith and Charlie Brown."

    result = run_agent(question=question, generated_sql=sql, final_answer=expected_answer)

    assert result["is_valid"] is True
    assert result["answer"] == expected_answer

    rows = ast.literal_eval(result["sql_output"])
    assert len(rows) >= 2
    for row in rows:
        assert row["country"] == "USA"


def test_agent_sql_order_by(run_agent):
    """Test agent handles ORDER BY clause sorting."""
    question = "List orders sorted by total amount in descending order."
    sql = "SELECT order_id, total_amount FROM orders ORDER BY total_amount DESC;"
    expected_answer = "Orders sorted by total amount from highest to lowest."

    result = run_agent(question=question, generated_sql=sql, final_answer=expected_answer)

    assert result["is_valid"] is True
    rows = ast.literal_eval(result["sql_output"])
    assert len(rows) >= 4
    amounts = [row["total_amount"] for row in rows]
    assert amounts == sorted(amounts, reverse=True)


def test_agent_sql_group_by_aggregation(run_agent):
    """Test agent handles GROUP BY with aggregation functions (COUNT, SUM)."""
    question = "What is the total order amount and count of orders for each status?"
    sql = "SELECT status, COUNT(*) AS order_count, SUM(total_amount) AS total_sum FROM orders GROUP BY status;"
    expected_answer = "Order breakdown by status."

    result = run_agent(question=question, generated_sql=sql, final_answer=expected_answer)

    assert result["is_valid"] is True
    rows = ast.literal_eval(result["sql_output"])
    statuses = [row["status"] for row in rows]
    assert "Shipped" in statuses
    assert "Pending" in statuses
    assert "Cancelled" in statuses


def test_agent_sql_join_tables(run_agent):
    """Test agent handles relational JOIN across customers and orders."""
    question = "Show each customer's name with their order ID and total amount."
    sql = """
    SELECT c.name, o.order_id, o.total_amount 
    FROM customers c 
    JOIN orders o ON c.customer_id = o.customer_id;
    """
    expected_answer = "List of customers with their corresponding orders."

    result = run_agent(question=question, generated_sql=sql, final_answer=expected_answer)

    assert result["is_valid"] is True
    rows = ast.literal_eval(result["sql_output"])
    assert len(rows) >= 4
    for row in rows:
        assert "name" in row
        assert "order_id" in row
        assert "total_amount" in row


def test_agent_sql_limit(run_agent):
    """Test agent handles LIMIT clause."""
    question = "Show the top 2 most expensive orders."
    sql = "SELECT order_id, total_amount FROM orders ORDER BY total_amount DESC LIMIT 2;"
    expected_answer = "Top 2 most expensive orders are 103 and 101."

    result = run_agent(question=question, generated_sql=sql, final_answer=expected_answer)

    assert result["is_valid"] is True
    rows = ast.literal_eval(result["sql_output"])
    assert len(rows) == 2


def test_agent_sql_like_pattern(run_agent):
    """Test agent handles LIKE pattern matching in WHERE clause."""
    question = "Find customers whose email contains 'alice'."
    sql = "SELECT customer_id, name, email FROM customers WHERE email LIKE '%alice%';"
    expected_answer = "Customer Alice Smith matches the email query."

    result = run_agent(question=question, generated_sql=sql, final_answer=expected_answer)

    assert result["is_valid"] is True
    rows = ast.literal_eval(result["sql_output"])
    assert len(rows) == 1
    assert rows[0]["name"] == "Alice Smith"


def test_agent_sql_multi_table_join(run_agent):
    """Test agent handles complex 4-table join across customers, orders, order_items, and products."""
    question = "Show customer names, the products they ordered, and the quantities."
    sql = """
    SELECT c.name AS customer_name, p.name AS product_name, oi.quantity, oi.unit_price
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id;
    """
    expected_answer = "Detailed line-item orders by customer."

    result = run_agent(question=question, generated_sql=sql, final_answer=expected_answer)

    assert result["is_valid"] is True
    rows = ast.literal_eval(result["sql_output"])
    assert len(rows) >= 5
    assert "customer_name" in rows[0]
    assert "product_name" in rows[0]
    assert "quantity" in rows[0]


def test_agent_sql_product_reviews_aggregation(run_agent):
    """Test agent handles review score aggregation per product."""
    question = "What is the average review rating and review count for each product?"
    sql = """
    SELECT p.name, ROUND(AVG(r.rating), 2) AS avg_rating, COUNT(r.review_id) AS review_count
    FROM products p
    JOIN reviews r ON p.product_id = r.product_id
    GROUP BY p.product_id, p.name
    HAVING COUNT(r.review_id) > 0
    ORDER BY avg_rating DESC;
    """
    expected_answer = "Average ratings and review counts per product."

    result = run_agent(question=question, generated_sql=sql, final_answer=expected_answer)

    assert result["is_valid"] is True
    rows = ast.literal_eval(result["sql_output"])
    assert len(rows) >= 3
    for row in rows:
        assert 1 <= row["avg_rating"] <= 5

