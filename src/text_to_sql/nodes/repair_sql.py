import logging
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from text_to_sql.llm import llm as default_llm
from text_to_sql.nodes.clean_sql import clean_sql_query
from text_to_sql.prompts import REPAIR_SQL_HUMAN_PROMPT, REPAIR_SQL_SYSTEM_PROMPT
from text_to_sql.state import AgentState

logger = logging.getLogger(__name__)


def repair_sql_query(
    sql_query: str,
    schema: str,
    question: str = "",
    validation_error: str | None = None,
    execution_error: str | None = None,
    diagnosis: str | None = None,
    retry_count: int = 1,
    model: BaseChatModel | None = None,
) -> str:
    """
    Repairs an invalid or failing SQL query based on original SQL, database schema,
    user question, and error feedback (validation error or execution error + diagnosis).
    """
    client = model if model is not None else default_llm

    error_items = []
    if validation_error:
        error_items.append(f"Validation Error:\n{validation_error}")
    if execution_error:
        error_items.append(f"Database Execution Error:\n{execution_error}")
    if diagnosis:
        error_items.append(f"Diagnostic Notes:\n{diagnosis}")

    if not error_items:
        error_items.append("Error: The query failed to execute properly.")

    error_details = "\n\n".join(error_items)

    system_prompt = REPAIR_SQL_SYSTEM_PROMPT
    user_prompt = REPAIR_SQL_HUMAN_PROMPT.format(
        schema=schema,
        question=question,
        sql_query=sql_query,
        error_details=error_details,
    )

    response = client.invoke(
        [
            SystemMessage(system_prompt),
            HumanMessage(user_prompt),
        ]
    )

    raw_sql = str(response.content)
    sql = clean_sql_query(raw_sql)

    return sql


def repair_sql(state: AgentState):
    """LangGraph node: Attempts self-repair of the SQL query using error diagnostic context."""
    question = state.get("question") or ""
    schema = state.get("schema")
    sql_query = state.get("sql_query")

    if schema is None:
        raise ValueError("[repair_sql] 'schema' is missing or None in state")
    if sql_query is None:
        raise ValueError("[repair_sql] 'sql_query' is missing or None in state")

    validation_error = state.get("validation_error")
    execution_error = state.get("execution_error")
    diagnosis = state.get("diagnosis")

    if validation_error:
        validation_retry_count = (state.get("validation_retry_count") or 0) + 1
    else:
        validation_retry_count = state.get("validation_retry_count") or 0

    try:
        sql = repair_sql_query(
            sql_query=sql_query,
            schema=schema,
            question=question,
            validation_error=validation_error,
            execution_error=execution_error,
            diagnosis=diagnosis,
        )
        logger.info("[repair_sql] Repaired SQL: %s", sql)
        return {
            "sql_query": sql,
            "validation_retry_count": validation_retry_count,
            "validation_error": None,
            "execution_error": None,
            "diagnosis": None,
        }
    except Exception as e:
        logger.error("[repair_sql] Failed to repair SQL: %s", e)
        raise
