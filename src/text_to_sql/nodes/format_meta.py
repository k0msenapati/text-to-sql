import logging
from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from text_to_sql.db import get_schema
from text_to_sql.llm import llm as default_llm
from text_to_sql.prompts import FORMAT_META_HUMAN_PROMPT, FORMAT_META_SYSTEM_PROMPT
from text_to_sql.state import AgentState

logger = logging.getLogger(__name__)


def format_meta_answer(
    question: str,
    schema: str,
    model: BaseChatModel | None = None,
) -> str:
    """
    Answers metadata questions using the database schema and natural language formatting.
    """
    client = model if model is not None else default_llm

    system_prompt = FORMAT_META_SYSTEM_PROMPT
    user_prompt = FORMAT_META_HUMAN_PROMPT.format(
        schema=schema,
        question=question,
    )

    response = client.invoke(
        [
            SystemMessage(system_prompt),
            HumanMessage(user_prompt),
        ]
    )

    return str(response.content)


def format_meta(state: AgentState):
    """LangGraph node: Formats answers for metadata/schema queries."""
    question = state.get("question")
    if not question or not question.strip():
        raise ValueError("[format_meta] 'question' is missing or empty in state")

    schema = state.get("schema")
    if not schema:
        schema = get_schema()

    try:
        answer = format_meta_answer(question=question, schema=schema)
        logger.info("[format_meta] Metadata answer formatted")
        return {
            "schema": schema,
            "answer": answer,
            "messages": [AIMessage(content=answer)],
        }
    except Exception as e:
        logger.error("[format_meta] Failed to format metadata answer: %s", e)
        raise
