from uuid import uuid4

from text_to_sql.db import get_schema, run_query, validate_sql_query
from text_to_sql.graph import agent
from text_to_sql.nodes import generate_sql_query, repair_sql_query


def test_llm_generates_valid_and_executable_sql():
    """
    Test that the LLM generates syntactically and semantically valid SQL
    that passes SQLite validation and successfully executes.
    """
    schema = str(get_schema())
    question = "List all customer names and their countries."

    sql = generate_sql_query(question=question, schema=schema)
    assert sql, "LLM should return a non-empty SQL query"

    validation = validate_sql_query(sql)
    assert validation["is_valid"] is True, f"Generated SQL failed validation: {sql} | Error: {validation['validation_error']}"

    rows = run_query(sql)
    assert len(rows) >= 3
    assert any("name" in k.lower() for k in rows[0].keys())


def test_llm_generates_correct_where_filter():
    """
    Test that the LLM correctly generates a WHERE filter for a condition.
    """
    schema = str(get_schema())
    question = "Find all orders with a total amount greater than 100."

    sql = generate_sql_query(question=question, schema=schema)
    validation = validate_sql_query(sql)
    assert validation["is_valid"] is True, f"Generated SQL failed validation: {sql} | Error: {validation['validation_error']}"

    rows = run_query(sql)
    assert len(rows) >= 1
    # Check that returned amounts are indeed > 100
    for row in rows:
        amount = row.get("total_amount")
        if amount is not None:
            assert amount > 100


def test_llm_generates_correct_join():
    """
    Test that the LLM correctly generates an explicit JOIN across related tables.
    """
    schema = str(get_schema())
    question = "Show each order ID together with the customer's name."

    sql = generate_sql_query(question=question, schema=schema)
    validation = validate_sql_query(sql)
    assert validation["is_valid"] is True, f"Generated SQL failed validation: {sql} | Error: {validation['validation_error']}"
    assert "JOIN" in sql.upper(), f"Expected query to use JOIN: {sql}"

    rows = run_query(sql)
    assert len(rows) >= 1


def test_llm_repairs_invalid_table_name():
    """
    Test that the LLM repairs an invalid query referencing a nonexistent table
    by consulting the database schema.
    """
    schema = str(get_schema())
    question = "List all clients."
    invalid_sql = "SELECT * FROM clients;"
    validation_error = "no such table: clients"

    repaired_sql = repair_sql_query(
        question=question,
        schema=schema,
        sql_query=invalid_sql,
        validation_error=validation_error,
        retry_count=1,
    )

    validation = validate_sql_query(repaired_sql)
    assert validation["is_valid"] is True, f"Repaired SQL is invalid: {repaired_sql} | Error: {validation['validation_error']}"
    assert "customers" in repaired_sql.lower()

    rows = run_query(repaired_sql)
    assert len(rows) >= 3


def test_llm_repairs_invalid_column_name():
    """
    Test that the LLM repairs an invalid query referencing a nonexistent column.
    """
    schema = str(get_schema())
    question = "Get customer full names."
    invalid_sql = "SELECT full_name FROM customers;"
    validation_error = "no such column: full_name"

    repaired_sql = repair_sql_query(
        question=question,
        schema=schema,
        sql_query=invalid_sql,
        validation_error=validation_error,
        retry_count=1,
    )

    validation = validate_sql_query(repaired_sql)
    assert validation["is_valid"] is True, f"Repaired SQL is invalid: {repaired_sql} | Error: {validation['validation_error']}"

    rows = run_query(repaired_sql)
    assert len(rows) >= 3


def test_agent_full_live_run():
    """
    Full end-to-end integration test of the agent using the live LLM,
    schema loading, validation, execution, and answer formatting.
    """
    config = {"configurable": {"thread_id": f"live-test-{uuid4()}"}}
    result = agent.invoke(
        {"question": "How many customers are located in the USA?"},
        config=config,
    )

    assert result["is_valid"] is True
    assert result["sql_query"] is not None
    assert result["sql_output"] is not None
    assert result["answer"] is not None
    assert len(result["answer"]) > 0
