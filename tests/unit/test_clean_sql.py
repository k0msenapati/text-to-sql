from text_to_sql.nodes.clean_sql import clean_sql_query


def test_clean_sql_query_standard_fences():
    raw = "```sql\nSELECT * FROM customers;\n```"
    assert clean_sql_query(raw) == "SELECT * FROM customers;"


def test_clean_sql_query_generic_fences():
    raw = "```\nSELECT * FROM orders;\n```"
    assert clean_sql_query(raw) == "SELECT * FROM orders;"


def test_clean_sql_query_with_introductory_and_trailing_text():
    raw = (
        "Here is the query you requested:\n"
        "```sql\n"
        "SELECT c.name, count(o.order_id) FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.name;\n"
        "```\n"
        "This joins customers and orders."
    )
    expected = "SELECT c.name, count(o.order_id) FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.name;"
    assert clean_sql_query(raw) == expected


def test_clean_sql_query_with_preface_without_fences():
    raw = "Sure, here is the query: SELECT * FROM products WHERE price > 50;"
    assert clean_sql_query(raw) == "SELECT * FROM products WHERE price > 50;"


def test_clean_sql_query_empty():
    assert clean_sql_query("") == ""
    assert clean_sql_query("   ") == ""
    assert clean_sql_query(None) == ""
