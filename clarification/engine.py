import logging
from typing import cast
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage
from pydantic import BaseModel, Field

from agent.model import llm as default_llm
from prompts import CLARIFICATION_HUMAN_PROMPT, CLARIFICATION_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class ClarificationOutput(BaseModel):
    """Result from the clarification engine."""

    can_resolve: bool = Field(
        description="True if the ambiguous query can be resolved/disambiguated using conversation history into a concrete database query; False otherwise."
    )
    resolved_query: str | None = Field(
        default=None,
        description="The rewritten, self-contained database query if can_resolve is True; otherwise None.",
    )
    clarification_question: str | None = Field(
        default=None,
        description="A polite question asking the user to clarify if can_resolve is False; otherwise None.",
    )
    options: list[str] = Field(
        default_factory=list,
        description="2 to 3 concrete interpretation options based on the database schema that the user might be looking for.",
    )


def format_message_history(messages: list[AnyMessage] | None) -> str:
    """Formats a list of LangChain/LangGraph messages into readable text for the prompt."""
    if not messages or len(messages) <= 1:
        return "No prior conversation history."

    formatted_lines = []
    # Exclude the current user question (last message)
    for msg in messages[:-1]:
        if isinstance(msg, HumanMessage):
            formatted_lines.append(f"User: {msg.content}")
        elif isinstance(msg, AIMessage):
            formatted_lines.append(f"Assistant: {msg.content}")
        else:
            formatted_lines.append(f"{msg.type.capitalize()}: {msg.content}")

    return (
        "\n".join(formatted_lines)
        if formatted_lines
        else "No prior conversation history."
    )


def format_clarification_response(result: ClarificationOutput) -> str:
    """Formats a friendly clarification message proposing numbered options."""
    intro = (
        result.clarification_question
        or "Your query is ambiguous. Could you please clarify what you'd like to see?"
    )
    if result.options:
        numbered_options = "\n".join(
            f"{i + 1}. {opt}" for i, opt in enumerate(result.options)
        )
        return f"{intro}\n\n{numbered_options}"
    return intro


def resolve_or_clarify_query(
    question: str,
    messages: list[AnyMessage] | None,
    schema: str,
    model: BaseChatModel | None = None,
) -> ClarificationOutput:
    """
    Analyzes an ambiguous query against conversation history and schema.
    Returns a ClarificationOutput indicating whether it was resolved or needs clarification.
    """
    client = model if model is not None else default_llm
    structured_llm = client.with_structured_output(ClarificationOutput)

    history_text = format_message_history(messages)
    system_prompt = CLARIFICATION_SYSTEM_PROMPT.format(schema=schema)
    user_prompt = CLARIFICATION_HUMAN_PROMPT.format(
        history=history_text,
        question=question,
    )

    result: ClarificationOutput = cast(
        ClarificationOutput,
        structured_llm.invoke(
            [
                SystemMessage(system_prompt),
                HumanMessage(user_prompt),
            ]
        ),
    )

    logger.info(
        "[resolve_or_clarify_query] can_resolve=%s | resolved_query=%s | options=%s",
        result.can_resolve,
        result.resolved_query,
        result.options,
    )
    return result
