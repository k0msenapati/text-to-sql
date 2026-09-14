import logging
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from agent.model import llm as default_llm
from prompts import FORMAT_META_HUMAN_PROMPT, FORMAT_META_SYSTEM_PROMPT

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
