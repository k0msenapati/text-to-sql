import logging

from text_to_sql.db import validate_sql_query
from text_to_sql.state import AgentState

logger = logging.getLogger(__name__)


def validate_sql(state: AgentState):
    """LangGraph node: Validates syntax and safety of the generated SQL query."""
    sql_query = state.get("sql_query")
    if not sql_query or not sql_query.strip():
        logger.warning("[validate_sql] 'sql_query' is missing or empty in state")
        return {
            "is_valid": False,
            "validation_error": "SQL query is missing or empty",
        }

    validation = validate_sql_query(sql_query)
    return {
        "is_valid": validation["is_valid"],
        "validation_error": validation["validation_error"],
    }
