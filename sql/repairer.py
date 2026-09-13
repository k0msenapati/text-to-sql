import logging
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from agent.model import llm as default_llm
from prompts import REPAIR_SQL_HUMAN_PROMPT, REPAIR_SQL_SYSTEM_PROMPT
from sql.cleaner import clean_sql_query

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
