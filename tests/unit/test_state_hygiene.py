from unittest.mock import MagicMock, patch
from uuid import uuid4
from langchain_core.messages import AIMessage, HumanMessage

from text_to_sql.graph import agent
from text_to_sql.nodes import QueryIntent


def test_transient_state_reset_across_turns():
    """
    Verify that transient execution state (sql_query, sql_output, etc.)
    does not leak into subsequent conversational turns over the same thread_id.
    """
    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    mock_classifier = MagicMock()
    mock_struct = MagicMock()
    # Turn 1: data_query, Turn 2: metadata_query
    mock_struct.invoke.side_effect = [
        QueryIntent(intent="data_query"),
        QueryIntent(intent="metadata_query"),
    ]
    mock_classifier.with_structured_output.return_value = mock_struct

    mock_generator = MagicMock()
    mock_generator.invoke.return_value = AIMessage(
        content="SELECT * FROM customers WHERE country = 'Canada';"
    )

    mock_formatter = MagicMock()
    mock_formatter.invoke.return_value = AIMessage(content="Found customers in Canada.")

    mock_meta = MagicMock()
    mock_meta.invoke.return_value = AIMessage(
        content="Database contains customers, orders."
    )

    with (
        patch("text_to_sql.nodes.classify.default_llm", mock_classifier),
        patch("text_to_sql.nodes.generate_sql.default_llm", mock_generator),
        patch("text_to_sql.nodes.format_answer.default_llm", mock_formatter),
        patch("text_to_sql.nodes.format_meta.default_llm", mock_meta),
    ):
        # Turn 1: Data query
        res1 = agent.invoke(
            {
                "question": "Show customers in Canada",
                "messages": [HumanMessage(content="Show customers in Canada")],
            },
            config=config,
        )
        assert res1["intent"] == "data_query"
        assert res1.get("sql_query") is not None
        assert res1.get("sql_output") is not None

        # Turn 2: Metadata query on the SAME thread_id
        res2 = agent.invoke(
            {
                "question": "What tables exist?",
                "messages": [HumanMessage(content="What tables exist?")],
            },
            config=config,
        )
        assert res2["intent"] == "metadata_query"
        # Verify transient fields from Turn 1 are NOT leaked into Turn 2
        assert res2.get("sql_query") is None
        assert res2.get("sql_output") is None
        assert res2.get("execution_error") is None
        assert res2.get("validation_error") is None
        assert res2["answer"] == "Database contains customers, orders."
