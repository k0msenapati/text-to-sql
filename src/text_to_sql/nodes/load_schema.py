import logging

from text_to_sql.db import get_schema
from text_to_sql.state import AgentState

logger = logging.getLogger(__name__)


def load_schema(state: AgentState):
    """LangGraph node: Loads the database schema into state."""
    try:
        schema = str(get_schema())
        logger.info("[load_schema] Schema loaded successfully")
        return {"schema": schema}
    except Exception as e:
        logger.error("[load_schema] Failed to load schema: %s", e)
        raise
