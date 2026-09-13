import logging
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from model import llm as default_llm
from prompts import REPAIR_SQL_HUMAN_PROMPT, REPAIR_SQL_SYSTEM_PROMPT
from sql.cleaner import clean_sql_query

logger = logging.getLogger(__name__)


def repair_sql_query(
    question: str,
    schema: str,
    sql_query: str,
    validation_error: str = "Unknown validation error",
    retry_count: int = 1,
    model: BaseChatModel | None = None,
) -> str:
    """
    Repairs an invalid SQL query based on database schema, user question, and validation error.
    """
    client = model if model is not None else default_llm

    system_prompt = REPAIR_SQL_SYSTEM_PROMPT
    user_prompt = REPAIR_SQL_HUMAN_PROMPT.format(
        schema=schema,
        question=question,
        sql_query=sql_query,
        validation_error=validation_error,
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
