from database import validate_sql_query


def test_agent_diagnoses_and_recovers_from_execution_error(run_agent):
    """
    Test that when a query passes static validation but triggers a database runtime error
    (e.g., malformed JSON in json_extract), the agent:
    1. Catches the error in execute_sql without crashing
    2. Routes to diagnose_execution_error to generate a diagnosis
    3. Routes to repair_sql with error and diagnosis
    4. Re-validates and successfully executes the repaired query
    """
    question = "Extract key from json."
    query_with_runtime_error = "SELECT json_extract('{bad_payload}', '$.val');"
    repaired_valid_sql = ["SELECT 'repaired_val' AS val;"]
    expected_answer = "Successfully extracted value after recovery."

    validation = validate_sql_query(query_with_runtime_error)
    assert validation["is_valid"] is True, "EXPLAIN validation passes on static syntax"

    result = run_agent(
        question=question,
        generated_sql=query_with_runtime_error,
        repaired_sql=repaired_valid_sql,
        final_answer=expected_answer,
        diagnosis="The JSON payload in json_extract is malformed. Replace with proper literal or valid column.",
    )

    assert result is not None
    assert result["is_valid"] is True
    assert result["execution_error"] is None
    assert result["execution_retry_count"] == 1
    assert result["answer"] == expected_answer
    assert "repaired_val" in result["sql_query"]


def test_agent_max_execution_retries_exhausted_does_not_crash(run_agent):
    """
    Test that when database runtime execution errors persist up to the retry limit (3),
    the agent does NOT crash with an unhandled exception, but routes to format_answer
    with an explanatory message detailing the execution error.
    """
    question = "Execute failing json function."
    query_with_runtime_error = "SELECT json_extract('{bad_json}', '$.a');"
    persistent_failing_repairs = [
        "SELECT json_extract('{bad_json_1}', '$.b');",
        "SELECT json_extract('{bad_json_2}', '$.c');",
        "SELECT json_extract('{bad_json_3}', '$.d');",
    ]

    result = run_agent(
        question=question,
        generated_sql=query_with_runtime_error,
        repaired_sql=persistent_failing_repairs,
        diagnosis="JSON function repeatedly fails due to invalid string argument.",
    )

    assert result is not None
    assert result["execution_error"] is not None
    assert "malformed JSON" in result["execution_error"]
    assert result["execution_retry_count"] == 3
    assert "unable to retrieve the data because a database execution error occurred" in result["answer"]
