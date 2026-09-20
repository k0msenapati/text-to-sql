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
    Executes a SQL query against the SQLite database.
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
