import logging
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: str):
        """Initializes the manager with the path to the SQLite file."""
        self.db_path = db_path

    def run_query(
        self, query: str, params: Optional[Tuple[Any, ...]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes any SQL query.
        Returns rows as a list of dictionaries (Column Name -> Value) for SELECT queries,
        or an empty list for write operations (INSERT, UPDATE, DELETE).
        """
        conn = sqlite3.connect(self.db_path)
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

    def get_schema(self) -> Dict[str, str]:
        """
        Retrieves the complete schema of the database.
        Returns a dictionary mapping the table/index name to its CREATE SQL statement.
        """
        query = "SELECT name, sql FROM sqlite_schema WHERE sql IS NOT NULL;"
        results = self.run_query(query)
        return {row["name"]: row["sql"] for row in results}

    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Retrieves column metadata (name, type, primary key status) for a specific table."""
        clean_name = "".join(c for c in table_name if c.isalnum() or c == "_")
        query = f"PRAGMA table_info({clean_name});"
        return self.run_query(query)


db_manager = DatabaseManager("data/example.db")


if __name__ == "__main__":
    print(db_manager.get_schema())
