from typing import Any

from text_to_sql.db.connection import DEFAULT_DB_PATH, run_query


def get_schema_dict(db_path: str = DEFAULT_DB_PATH) -> dict[str, str]:
    """Retrieves the complete schema of the database as table/index name -> CREATE SQL statement."""
    query = "SELECT name, sql FROM sqlite_schema WHERE sql IS NOT NULL;"
    results = run_query(query, db_path=db_path)
    return {row["name"]: row["sql"] for row in results}


def get_schema(db_path: str = DEFAULT_DB_PATH) -> str:
    """Retrieves and formats the complete database schema as clean SQL DDL statements."""
    schema_dict = get_schema_dict(db_path=db_path)
    ddl_statements = []
    for table_name, create_sql in schema_dict.items():
        clean_ddl = create_sql.strip().rstrip(";") + ";"
        ddl_statements.append(f"-- Table: {table_name}\n{clean_ddl}")
    return "\n\n".join(ddl_statements)


def get_formatted_schema(db_path: str = DEFAULT_DB_PATH) -> str:
    """Alias for get_schema to preserve backwards compatibility."""
    return get_schema(db_path=db_path)


def get_table_columns(
    table_name: str, db_path: str = DEFAULT_DB_PATH
) -> list[dict[str, Any]]:
    """Retrieves column metadata for a specific table."""
    clean_name = "".join(c for c in table_name if c.isalnum() or c == "_")
    return run_query(f"PRAGMA table_info({clean_name});", db_path=db_path)
