import logging
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from text_to_sql.llm import llm as default_llm
from text_to_sql.prompts import (
    DIAGNOSE_EXECUTION_ERROR_HUMAN_PROMPT,
    DIAGNOSE_EXECUTION_ERROR_SYSTEM_PROMPT,
)
from text_to_sql.state import AgentState

logger = logging.getLogger(__name__)


def diagnose_execution_error_query(
    sql_query: str,
    execution_error: str,
    schema: str,
    model: BaseChatModel | None = None,
) -> str:
    """
    Diagnoses a database runtime execution error given the failed SQL query,
    the error message raised by SQLite, and the database schema.
    Returns an expert diagnostic explanation of the issue and how to resolve it.
    """
    client = model if model is not None else default_llm

    system_prompt = DIAGNOSE_EXECUTION_ERROR_SYSTEM_PROMPT
    user_prompt = DIAGNOSE_EXECUTION_ERROR_HUMAN_PROMPT.format(
        schema=schema,
        sql_query=sql_query,
        execution_error=execution_error,
    )

    response = client.invoke(
        [
            SystemMessage(system_prompt),
            HumanMessage(user_prompt),
        ]
    )

    diagnosis = str(response.content).strip()
    return diagnosis


def diagnose_execution_error(state: AgentState):
    """LangGraph node: Analyzes SQLite runtime errors and formulates diagnosis for repair."""
    sql_query = state.get("sql_query")
    execution_error = state.get("execution_error") or "Unknown database execution error"
    schema = state.get("schema")

    if not sql_query or not sql_query.strip():
        raise ValueError(
            "[diagnose_execution_error] 'sql_query' is missing or empty in state"
        )
    if schema is None:
        raise ValueError(
            "[diagnose_execution_error] 'schema' is missing or None in state"
        )

    execution_retry_count = (state.get("execution_retry_count") or 0) + 1

    try:
        diagnosis = diagnose_execution_error_query(
            sql_query=sql_query,
            execution_error=execution_error,
            schema=schema,
        )
        logger.info(
            "[diagnose_execution_error] Retry %d/3 - Diagnosis: %s",
            execution_retry_count,
            diagnosis,
        )
        return {
            "diagnosis": diagnosis,
            "execution_retry_count": execution_retry_count,
        }
    except Exception as e:
        logger.error(
            "[diagnose_execution_error] Failed to diagnose execution error: %s", e
        )
        raise
