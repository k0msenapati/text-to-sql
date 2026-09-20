import logging
from typing import Literal, cast
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from text_to_sql.llm import llm as default_llm
from text_to_sql.prompts import CLASSIFY_INTENT_SYSTEM_PROMPT
from text_to_sql.state import AgentState

logger = logging.getLogger(__name__)

IntentType = Literal[
    "data_query",
    "metadata_query",
    "ambiguous_query",
    "out_of_scope_query",
]

VALID_INTENTS = {
    "data_query",
    "metadata_query",
    "ambiguous_query",
    "out_of_scope_query",
}


class QueryIntent(BaseModel):
    """Classification of the user's natural language query intent."""

    intent: IntentType = Field(
        description=(
            "The classified category of the query: "
            "'data_query' for queries asking to retrieve, aggregate, filter, or calculate data records from the database; "
            "'metadata_query' for questions about database structure, schema, tables, columns, types, or relationships; "
            "'ambiguous_query' for vague, underspecified requests that lack sufficient context to determine what is being asked; "
            "'out_of_scope_query' for general knowledge, conversation, or requests unrelated to the database."
        )
    )


def classify_query_intent(
    question: str,
    model: BaseChatModel | None = None,
) -> str:
    """Classifies query intent using structured output."""
    client = model if model is not None else default_llm
    structured_llm = client.with_structured_output(QueryIntent)

    result: QueryIntent = cast(
        QueryIntent,
        structured_llm.invoke(
            [
                SystemMessage(CLASSIFY_INTENT_SYSTEM_PROMPT),
                HumanMessage(question),
            ]
        ),
    )

    logger.info(
        "[classify_query_intent] Query: '%s' -> Intent: '%s'", question, result.intent
    )
    return result.intent


def classify_intent(state: AgentState):
    """LangGraph node: Classifies the intent of the incoming user question."""
    messages = state.get("messages") or []
    question = state.get("question")
    if not question and messages:
        question = str(messages[-1].content)

    if not question or not question.strip():
        raise ValueError("[classify_intent] 'question' is missing or empty in state")

    try:
        intent = classify_query_intent(question=question)
        logger.info("[classify_intent] Classified intent: %s", intent)

        updates: dict[str, str | list] = {"intent": intent, "question": question}
        if not messages or messages[-1].content != question:
            updates["messages"] = [HumanMessage(content=question)]
        return updates
    except Exception as e:
        logger.error("[classify_intent] Failed to classify intent: %s", e)
        raise
