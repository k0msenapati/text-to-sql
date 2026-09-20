import logging
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from text_to_sql.llm import llm as default_llm
from text_to_sql.nodes.clarify import format_message_history
from text_to_sql.nodes.clean_sql import clean_sql_query
from text_to_sql.prompts import GENERATE_SQL_HUMAN_PROMPT, GENERATE_SQL_SYSTEM_PROMPT
from text_to_sql.state import AgentState

logger = logging.getLogger(__name__)


def generate_sql_query(
    question: str,
    schema: str,
    history: str = "No prior conversation history.",
    database_dialect: str = "sqlite",
    model: BaseChatModel | None = None,
) -> str:
    """
    Generates a SQL query from a natural language question, database schema,
    and conversation history using the LLM.
    """
    client = model if model is not None else default_llm

    system_prompt = GENERATE_SQL_SYSTEM_PROMPT.format(database_dialect=database_dialect)
    user_prompt = GENERATE_SQL_HUMAN_PROMPT.format(
        schema=schema,
        history=history,
        question=question,
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


def generate_sql(state: AgentState) -> AgentState:
    """LangGraph node: Generates an initial SQL query based on the question, schema, and history."""
    question = state.get("question")
    if not question or not question.strip():
        raise ValueError("[generate_sql] 'question' is missing or empty in state")

    schema = state.get("schema")
    if schema is None:
        raise ValueError("[generate_sql] 'schema' is missing or None in state")

    messages = state.get("messages") or []
    history = format_message_history(messages)

    try:
        sql = generate_sql_query(question=question, schema=schema, history=history)
        logger.info("[generate_sql] Generated SQL: %s", sql)
        return {
            "sql_query": sql,
            "validation_retry_count": 0,
            "execution_retry_count": 0,
            "execution_error": None,
            "diagnosis": None,
        }
    except Exception as e:
        logger.error("[generate_sql] Failed to generate SQL: %s", e)
        raise
