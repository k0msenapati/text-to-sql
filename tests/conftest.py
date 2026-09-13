from unittest.mock import MagicMock, patch
from uuid import uuid4
import pytest
from langchain_core.messages import AIMessage

from agent.agent import agent


@pytest.fixture
def run_agent():
    """
    Helper fixture to execute the text-to-sql agent with deterministic LLM responses.
    """
    def _executor(
        question: str,
        generated_sql: str,
        repaired_sql: list[str] | None = None,
        final_answer: str = "Here is the result based on your query.",
    ):
        mock_generator = MagicMock()
        mock_generator.invoke.return_value = AIMessage(content=generated_sql)

        mock_repairer = MagicMock()
        if repaired_sql:
            mock_repairer.invoke.side_effect = [
                AIMessage(content=sql) for sql in repaired_sql
            ]
        else:
            mock_repairer.invoke.return_value = AIMessage(content=generated_sql)

        mock_formatter = MagicMock()
        mock_formatter.invoke.return_value = AIMessage(content=final_answer)

        config = {"configurable": {"thread_id": str(uuid4())}}

        with (
            patch("sql.generator.default_llm", mock_generator),
            patch("sql.repairer.default_llm", mock_repairer),
            patch("sql.formatter.default_llm", mock_formatter),
        ):
            return agent.invoke({"question": question}, config=config)

    return _executor
