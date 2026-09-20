import logging

from text_to_sql.db import run_query
from text_to_sql.state import AgentState

logger = logging.getLogger(__name__)


def execute_sql(state: AgentState):
    """LangGraph node: Executes the validated SQL query against the SQLite database."""
    sql_query = state.get("sql_query")
    if not sql_query or not sql_query.strip():
        raise ValueError("[execute_sql] 'sql_query' is missing or empty in state")

    try:
        sql_output = run_query(sql_query)
        logger.info("[execute_sql] SQL executed: %d row(s) returned", len(sql_output))
        return {
            "sql_output": str(sql_output),
            "execution_error": None,
        }
    except Exception as e:
        logger.warning(
            "[execute_sql] Database execution failed for query '%s': %s", sql_query, e
        )
        return {
            "sql_output": None,
            "execution_error": str(e),
        }
