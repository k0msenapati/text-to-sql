import logging
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from model import llm as default_llm
from prompts import FORMAT_ANSWER_HUMAN_PROMPT, FORMAT_ANSWER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def format_sql_answer(
    question: str,
    sql_query: str,
    sql_output: str,
    model: BaseChatModel | None = None,
) -> str:
    """
    Transforms raw SQL execution results into a clean, natural language response using the LLM.
    """
    client = model if model is not None else default_llm

    system_prompt = FORMAT_ANSWER_SYSTEM_PROMPT
    user_prompt = FORMAT_ANSWER_HUMAN_PROMPT.format(
        question=question,
        sql_query=sql_query,
        sql_output=sql_output,
    )

    response = client.invoke(
        [
            SystemMessage(system_prompt),
            HumanMessage(user_prompt),
        ]
    )

    return str(response.content)
