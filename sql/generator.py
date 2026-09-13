import logging
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from agent.model import llm as default_llm
from prompts import GENERATE_SQL_HUMAN_PROMPT, GENERATE_SQL_SYSTEM_PROMPT
from sql.cleaner import clean_sql_query

logger = logging.getLogger(__name__)


def generate_sql_query(
    question: str,
    schema: str,
    database_dialect: str = "sqlite",
    model: BaseChatModel | None = None,
) -> str:
    """
    Generates a SQL query from a natural language question and database schema using the LLM.
    """
    client = model if model is not None else default_llm

    system_prompt = GENERATE_SQL_SYSTEM_PROMPT.format(database_dialect=database_dialect)
    user_prompt = GENERATE_SQL_HUMAN_PROMPT.format(schema=schema, question=question)

    response = client.invoke(
        [
            SystemMessage(system_prompt),
            HumanMessage(user_prompt),
        ]
    )

    raw_sql = str(response.content)
    sql = clean_sql_query(raw_sql)

    return sql
