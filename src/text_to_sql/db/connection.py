import logging
import os
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "data/example.db"


def get_connection(
    db_path: str = DEFAULT_DB_PATH, read_only: bool = True
) -> sqlite3.Connection:
    """Creates a SQLite connection, defaulting to read-only URI mode for query safety."""
    if db_path == ":memory:":
        conn = sqlite3.connect(":memory:")
    elif read_only:
        abs_path = os.path.abspath(db_path)
        conn = sqlite3.connect(f"file:{abs_path}?mode=ro", uri=True)
    else:
        conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def run_query(
    query: str,
    params: tuple[Any, ...] | None = None,
    db_path: str = DEFAULT_DB_PATH,
) -> list[dict[str, Any]]:
    """
    Executes a SQL query against the SQLite database in read-only mode.
    Returns rows as a list of dictionaries (Column Name -> Value) for SELECT queries.
    """
    conn = get_connection(db_path=db_path, read_only=True)
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
