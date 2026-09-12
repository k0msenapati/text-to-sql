import sqlite3
from typing import Any, Dict, Optional

from database.db_manager import DatabaseManager, db_manager


class SQLValidator:
    def __init__(self):
        self.db = db_manager

    def validate(self, query: str) -> Dict[str, Any]:
        """Validates that a query is non-empty, a SELECT statement, syntactically correct, and references existing tables/columns."""
        if not query or not query.strip():
            return {"is_valid": False, "validation_error": "Query cannot be empty"}

        clean_query = query.strip().rstrip(";")

        # Only allow SELECT queries
        if not clean_query.lower().startswith("select"):
            return {"is_valid": False, "validation_error": "Only SELECT queries are allowed"}

        # SQLite EXPLAIN validates syntax and verifies existing tables and columns
        conn = sqlite3.connect(self.db.db_path)
        try:
            conn.cursor().execute(f"EXPLAIN {clean_query}")
            return {"is_valid": True, "validation_error": None}
        except sqlite3.OperationalError as e:
            return {"is_valid": False, "validation_error": str(e)}
        finally:
            conn.close()


sql_validator = SQLValidator()


def validate_sql_query(query: str) -> Dict[str, Any]:
    return sql_validator.validate(query)
