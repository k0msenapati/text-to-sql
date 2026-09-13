import sqlite3
from uuid import uuid4
import pytest

from agent.agent import agent
from database import validate_sql_query


def test_current_agent_crashes_on_runtime_execution_error(run_agent):
    """
    Demonstrates the architectural limitation of the CURRENT agent:
    
    1. A query passes EXPLAIN validation (e.g. `SELECT json_extract('{malformed}', '$.key')`).
       `validate_sql` marks `is_valid: True` because SQLite EXPLAIN only verifies static syntax.
    2. LangGraph routes to `execute_sql`.
    3. At runtime, SQLite raises `sqlite3.OperationalError: malformed JSON`.
    4. Because the agent only has static validation and lacks `diagnose_exec_error`,
       `execute_sql` raises an unhandled exception and the entire agent crashes.
       
    This test asserts that the current agent crashes with sqlite3.OperationalError,
    confirming why the `diagnose_exec_error` feature is needed.
    """
    question = "Extract key from malformed data."
    # This query passes EXPLAIN validation, but fails during actual SQLite execution
    query_with_runtime_error = "SELECT json_extract('{malformed_data}', '$.key');"

    # 1. Verify that validation falsely thinks this query is valid
    validation = validate_sql_query(query_with_runtime_error)
    assert validation["is_valid"] is True, "EXPLAIN validation passes on this query"

    # 2. Verify that the current agent fails and raises an unhandled exception
    with pytest.raises(sqlite3.OperationalError, match="malformed JSON"):
        run_agent(
            question=question,
            generated_sql=query_with_runtime_error,
        )


@pytest.mark.xfail(
    reason=(
        "EXPECTED TO FAIL: The current agent lacks a 'diagnose_exec_error' node. "
        "When an execution error occurs at runtime, the agent crashes instead of "
        "diagnosing the error and routing to repair."
    ),
    strict=True,
    raises=sqlite3.OperationalError,
)
def test_agent_diagnoses_and_recovers_from_execution_error(run_agent):
    """
    This test will PASS in the future once `diagnose_exec_error` is implemented.
    Currently, it FAILS (marked as strict xfail) because the agent does not catch
    or diagnose runtime execution errors.
    """
    question = "Extract key from json."
    query_with_runtime_error = "SELECT json_extract('{bad_payload}', '$.val');"

    # Expected behavior once diagnose_exec_error is added:
    # The agent should NOT raise an unhandled exception, but diagnose the error
    # and either repair or return an explanatory answer.
    result = run_agent(
        question=question,
        generated_sql=query_with_runtime_error,
    )

    # In the current agent, execution never reaches here; it crashes above.
    assert result is not None
    assert "answer" in result
