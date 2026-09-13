import logging
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "data/example.db"


def run_query(
    query: str,
    params: tuple[Any, ...] | None = None,
    db_path: str = DEFAULT_DB_PATH,
) -> list[dict[str, Any]]:
    """
    Executes a SQL query against SQLite database.
    Returns rows as a list of dictionaries (Column Name -> Value) for SELECT queries,
    or an empty list for write operations.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        with conn:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if cursor.description:
                return [dict(row) for row in cursor.fetchall()]
            return []
    except sqlite3.Error as e:
        logger.error("Database query failed: %s | Error: %s", query, e)
        raise
    finally:
        conn.close()


def get_schema(db_path: str = DEFAULT_DB_PATH) -> dict[str, str]:
    """Retrieves the complete schema of the database as table/index name -> CREATE SQL statement."""
    query = "SELECT name, sql FROM sqlite_schema WHERE sql IS NOT NULL;"
    results = run_query(query, db_path=db_path)
    return {row["name"]: row["sql"] for row in results}


def get_table_columns(
    table_name: str, db_path: str = DEFAULT_DB_PATH
) -> list[dict[str, Any]]:
    """Retrieves column metadata for a specific table."""
    clean_name = "".join(c for c in table_name if c.isalnum() or c == "_")
    return run_query(f"PRAGMA table_info({clean_name});", db_path=db_path)
