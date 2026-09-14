import logging
from typing import Literal, cast
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from agent.model import llm as default_llm
from prompts import CLASSIFY_INTENT_SYSTEM_PROMPT

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
