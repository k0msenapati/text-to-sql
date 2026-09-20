from text_to_sql.db.validator import validate_sql_query


def test_validate_sql_query_allows_ctes():
    """Verify that Common Table Expressions (WITH queries) are accepted as valid."""
    cte_query = """
    WITH customer_spending AS (
        SELECT customer_id, SUM(total_amount) AS total
        FROM orders
        GROUP BY customer_id
    )
    SELECT c.name, cs.total
    FROM customers c
    JOIN customer_spending cs ON c.customer_id = cs.customer_id;
    """
    res = validate_sql_query(cte_query)
    assert res["is_valid"] is True
    assert res["validation_error"] is None


def test_validate_sql_query_allows_leading_comments():
    """Verify that queries with leading comments are accepted."""
    commented_query = """
    -- Retrieve all customers from Canada
    /* multi-line
       comment */
    SELECT name, country FROM customers WHERE country = 'Canada';
    """
    res = validate_sql_query(commented_query)
    assert res["is_valid"] is True
    assert res["validation_error"] is None


def test_validate_sql_query_rejects_multiple_statements():
    """Verify that semicolon-chained multiple statements are rejected."""
    multi_query = "SELECT 1; DROP TABLE customers;"
    res = validate_sql_query(multi_query)
    assert res["is_valid"] is False
    assert "Multiple SQL statements" in (res["validation_error"] or "")


def test_validate_sql_query_allows_semicolon_in_string():
    """Verify that semicolons inside string literals do not trigger false multiple statement errors."""
    query = "SELECT * FROM customers WHERE email = 'test;with;semicolon@example.com';"
    res = validate_sql_query(query)
    assert res["is_valid"] is True
    assert res["validation_error"] is None
