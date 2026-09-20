from unittest.mock import MagicMock, patch
from uuid import uuid4
import pytest
from langchain_core.messages import AIMessage

from text_to_sql.graph import agent
from text_to_sql.nodes import QueryIntent


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
        diagnosis: str = "The SQL query encountered a runtime error and requires modification.",
        intent: str = "data_query",
    ):
        mock_classifier_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = QueryIntent(intent=intent)
        mock_classifier_llm.with_structured_output.return_value = mock_structured_llm

        mock_generator = MagicMock()
        mock_generator.invoke.return_value = AIMessage(content=generated_sql)

        mock_repairer = MagicMock()
        if repaired_sql:
            mock_repairer.invoke.side_effect = [
                AIMessage(content=sql) for sql in repaired_sql
            ]
        else:
            mock_repairer.invoke.return_value = AIMessage(content=generated_sql)

        mock_diagnoser = MagicMock()
        mock_diagnoser.invoke.return_value = AIMessage(content=diagnosis)

        mock_formatter = MagicMock()
        mock_formatter.invoke.return_value = AIMessage(content=final_answer)

        config = {"configurable": {"thread_id": str(uuid4())}}

        with (
            patch("text_to_sql.nodes.classify.default_llm", mock_classifier_llm),
            patch("text_to_sql.nodes.generate_sql.default_llm", mock_generator),
            patch("text_to_sql.nodes.repair_sql.default_llm", mock_repairer),
            patch("text_to_sql.nodes.diagnose.default_llm", mock_diagnoser),
            patch("text_to_sql.nodes.format_answer.default_llm", mock_formatter),
        ):
            return agent.invoke({"question": question}, config=config)

    return _executor
