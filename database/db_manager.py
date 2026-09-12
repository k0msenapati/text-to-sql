import logging
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: str = "data/example.db"):
        self.db_path = db_path

    def run_query(
        self, query: str, params: Optional[Tuple[Any, ...]] = None
    ) -> List[Dict[str, Any]]:
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
        query = "SELECT name, sql FROM sqlite_schema WHERE sql IS NOT NULL;"
        results = self.run_query(query)
        return {row["name"]: row["sql"] for row in results}

    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        clean_name = "".join(c for c in table_name if c.isalnum() or c == "_")
        return self.run_query(f"PRAGMA table_info({clean_name});")


db_manager = DatabaseManager()
