import sqlite3
import pytest

from text_to_sql.db.connection import get_connection, run_query


def test_connection_read_only_mode():
    """Verify that SQLite connection is established in read-only mode and blocks write operations."""
    # SELECT works
    rows = run_query("SELECT 1 AS num;")
    assert len(rows) == 1
    assert rows[0]["num"] == 1

    # Mutation fails with OperationalError (attempt to write a readonly database)
    with pytest.raises(sqlite3.OperationalError, match="readonly database"):
        run_query("CREATE TABLE malicious_test (id INTEGER);")


def test_memory_connection_fallback():
    """Verify in-memory SQLite connection works."""
    conn = get_connection(":memory:")
    assert isinstance(conn, sqlite3.Connection)
    conn.close()
