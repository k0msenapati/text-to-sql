import ast


def test_agent_recovers_from_invalid_table_name(run_agent):
    """
    Test agent catches a validation error for a nonexistent table,
    routes to repair_sql, generates valid SQL, and finishes without crashing.
    """
    question = "Show all users."
    invalid_sql = "SELECT * FROM users;"  # table does not exist
    repaired_sql = ["SELECT * FROM customers;"]
    expected_answer = "Found customer records."

    result = run_agent(
        question=question,
        generated_sql=invalid_sql,
        repaired_sql=repaired_sql,
        final_answer=expected_answer,
    )

    assert result["is_valid"] is True
    assert result["retry_count"] == 1
    assert "customers" in result["sql_query"]
    assert result["answer"] == expected_answer

    rows = ast.literal_eval(result["sql_output"])
    assert len(rows) >= 3


def test_agent_rejects_non_select_and_repairs(run_agent):
    """
    Test agent rejects non-SELECT queries (e.g. DELETE/DROP) at validation stage,
    safely repairs to a SELECT query, and does not crash.
    """
    question = "Remove customer 1."
    destructive_sql = "DELETE FROM customers WHERE customer_id = 1;"
    repaired_sql = ["SELECT * FROM customers WHERE customer_id = 1;"]
    expected_answer = "Details for customer 1."

    result = run_agent(
        question=question,
        generated_sql=destructive_sql,
        repaired_sql=repaired_sql,
        final_answer=expected_answer,
    )

    assert result["is_valid"] is True
    assert result["retry_count"] == 1
    assert "SELECT" in result["sql_query"].upper()
    assert "DELETE" not in result["sql_query"].upper()


def test_agent_recovers_from_syntax_error(run_agent):
    """
    Test agent catches a syntax error during EXPLAIN validation,
    routes to repair, and recovers gracefully without crashing.
    """
    question = "List customer names."
    broken_sql = "SELECT name customers WHERE;"  # syntax error
    repaired_sql = ["SELECT name FROM customers;"]
    expected_answer = "Customer names list."

    result = run_agent(
        question=question,
        generated_sql=broken_sql,
        repaired_sql=repaired_sql,
        final_answer=expected_answer,
    )

    assert result["is_valid"] is True
    assert result["retry_count"] == 1
    assert result["answer"] == expected_answer


def test_agent_max_retries_exhausted_does_not_crash(run_agent):
    """
    Test agent handles persistent validation errors up to max retry limit (3),
    routes to format_answer with a polite explanation, and does NOT crash.
    """
    question = "Find data in missing tables."
    initial_sql = "SELECT * FROM ghost_table_1;"
    persistent_invalid_repairs = [
        "SELECT * FROM ghost_table_2;",
        "SELECT * FROM ghost_table_3;",
        "SELECT * FROM ghost_table_4;",
    ]

    result = run_agent(
        question=question,
        generated_sql=initial_sql,
        repaired_sql=persistent_invalid_repairs,
    )

    assert result["is_valid"] is False
    assert result["retry_count"] == 3
    assert result["validation_error"] is not None
    assert "no such table" in result["validation_error"]
    assert "unable to retrieve the data because the SQL query could not be validated" in result["answer"]


def test_agent_handles_empty_generated_query_and_repairs(run_agent):
    """
    Test agent handles empty SQL generation, flags it in validation,
    and successfully recovers via repair without crashing.
    """
    question = "Show orders."
    empty_sql = "   "
    repaired_sql = ["SELECT * FROM orders;"]
    expected_answer = "All orders list."

    result = run_agent(
        question=question,
        generated_sql=empty_sql,
        repaired_sql=repaired_sql,
        final_answer=expected_answer,
    )

    assert result["is_valid"] is True
    assert result["retry_count"] == 1
    assert "SELECT * FROM orders;" in result["sql_query"]
    assert result["answer"] == expected_answer
