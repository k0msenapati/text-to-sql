import logging
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from agent.model import llm as default_llm
from prompts import (
    DIAGNOSE_EXECUTION_ERROR_HUMAN_PROMPT,
    DIAGNOSE_EXECUTION_ERROR_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


def diagnose_execution_error(
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
