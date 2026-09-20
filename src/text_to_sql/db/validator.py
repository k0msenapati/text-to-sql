import sqlite3
from typing import TypedDict

from text_to_sql.db.connection import DEFAULT_DB_PATH


class ValidationResult(TypedDict):
    is_valid: bool
    validation_error: str | None


def validate_sql_query(
    query: str, db_path: str = DEFAULT_DB_PATH
) -> ValidationResult:
    """
    Validates that a query is non-empty, a SELECT statement, syntactically correct,
    and references existing tables/columns in SQLite.
    """
    if not query or not query.strip():
        return {"is_valid": False, "validation_error": "Query cannot be empty"}

    clean_query = query.strip().rstrip(";")

    # Only allow SELECT queries
    if not clean_query.lower().startswith("select"):
        return {"is_valid": False, "validation_error": "Only SELECT queries are allowed"}

    # SQLite EXPLAIN validates syntax and verifies existing tables and columns
    conn = sqlite3.connect(db_path)
    try:
        conn.cursor().execute(f"EXPLAIN {clean_query}")
        return {"is_valid": True, "validation_error": None}
    except sqlite3.OperationalError as e:
        return {"is_valid": False, "validation_error": str(e)}
    finally:
        conn.close()
