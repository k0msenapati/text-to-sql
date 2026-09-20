import logging
from langchain_core.messages import AIMessage

from text_to_sql.state import AgentState

logger = logging.getLogger(__name__)

OUT_OF_SCOPE_FALLBACK_MESSAGE = (
    "I am a Text-to-SQL assistant designed to answer questions about the database. "
    "Your request is out of scope. Please ask a database-related question."
)


def handle_out_of_scope_query(state: AgentState):
    """LangGraph node: Handles out-of-scope non-database queries with a standard fallback message."""
    logger.info("[handle_out_of_scope_query] Handling out-of-scope query")
    return {
        "answer": OUT_OF_SCOPE_FALLBACK_MESSAGE,
        "messages": [AIMessage(content=OUT_OF_SCOPE_FALLBACK_MESSAGE)],
    }
