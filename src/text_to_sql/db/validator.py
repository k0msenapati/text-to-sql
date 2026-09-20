import re
import sqlite3
from typing import TypedDict

from text_to_sql.db.connection import DEFAULT_DB_PATH, get_connection


class ValidationResult(TypedDict):
    is_valid: bool
    validation_error: str | None


def _strip_comments(sql: str) -> str:
    """Removes SQL line comments and block comments."""
    # Remove block comments /* ... */
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    # Remove line comments -- ...
    sql = re.sub(r"--[^\n]*", "", sql)
    return sql.strip()


def _has_multiple_statements(sql: str) -> bool:
    """Detects if multiple SQL statements are present outside string literals."""
    # Strip comments first
    clean = _strip_comments(sql)
    # Strip single-quoted string literals (handling escaped quotes '')
    clean = re.sub(r"'(''|[^'])*'", "''", clean)
    # Strip double-quoted identifiers
    clean = re.sub(r'"(""|[^"])*"', '""', clean)
    # Strip trailing whitespace and trailing semicolons
    clean = clean.strip().rstrip(";").strip()
    return ";" in clean


def validate_sql_query(query: str, db_path: str = DEFAULT_DB_PATH) -> ValidationResult:
    """
    Validates that a query is non-empty, a read-only SELECT or WITH statement,
    syntactically correct, and references existing tables/columns in SQLite.
    """
    if not query or not query.strip():
        return {"is_valid": False, "validation_error": "Query cannot be empty"}

    if _has_multiple_statements(query):
        return {
            "is_valid": False,
            "validation_error": "Multiple SQL statements are not allowed",
        }

    clean_query = query.strip().rstrip(";")
    uncommented = _strip_comments(clean_query)

    # Only allow SELECT or CTE (WITH) queries
    if not (
        uncommented.lower().startswith("select")
        or uncommented.lower().startswith("with")
    ):
        return {
            "is_valid": False,
            "validation_error": "Only SELECT queries are allowed",
        }

    # SQLite EXPLAIN validates syntax and verifies existing tables and columns
    conn = get_connection(db_path=db_path, read_only=True)
    try:
        conn.cursor().execute(f"EXPLAIN {clean_query}")
        return {"is_valid": True, "validation_error": None}
    except sqlite3.OperationalError as e:
        return {"is_valid": False, "validation_error": str(e)}
    finally:
        conn.close()
