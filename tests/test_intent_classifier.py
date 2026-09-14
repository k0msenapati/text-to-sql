from unittest.mock import MagicMock, patch
from uuid import uuid4
from langchain_core.messages import AIMessage

from agent.agent import agent
from agent.nodes import OUT_OF_SCOPE_FALLBACK_MESSAGE
from classifier import QueryIntent, classify_query_intent
from metadata import format_meta_answer


def test_classify_query_intent_mocked():
    """Test classify_query_intent function with structured LLM output."""
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = QueryIntent(intent="metadata_query")
    mock_llm.with_structured_output.return_value = mock_structured

    intent = classify_query_intent("What tables exist?", model=mock_llm)
    assert intent == "metadata_query"
    mock_llm.with_structured_output.assert_called_once_with(QueryIntent)


def test_agent_routes_to_metadata_query():
    """Test agent routes metadata_query to format_meta and returns formatted schema answer."""
    question = "What tables are in the database?"
    expected_meta_answer = "The database contains categories, products, customers, orders, order_items, and reviews."

    mock_classifier_llm = MagicMock()
    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.return_value = QueryIntent(intent="metadata_query")
    mock_classifier_llm.with_structured_output.return_value = mock_structured_llm

    mock_meta_llm = MagicMock()
    mock_meta_llm.invoke.return_value = AIMessage(content=expected_meta_answer)

    config = {"configurable": {"thread_id": str(uuid4())}}

    with (
        patch("classifier.classifier.default_llm", mock_classifier_llm),
        patch("metadata.formatter.default_llm", mock_meta_llm),
    ):
        result = agent.invoke({"question": question}, config=config)

    assert result["intent"] == "metadata_query"
    assert result["answer"] == expected_meta_answer
    assert result["schema"] is not None
    # Verify SQL generation / execution was bypassed
    assert result.get("sql_query") is None
    assert result.get("sql_output") is None


def test_agent_routes_to_ambiguous_query():
    """Test agent routes ambiguous_query to clarification_engine and returns clarifying question."""
    question = "Can you show that?"
    clarifying_question = "What would you like to see? 1. Customers 2. Orders"

    mock_classifier_llm = MagicMock()
    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.return_value = QueryIntent(intent="ambiguous_query")
    mock_classifier_llm.with_structured_output.return_value = mock_structured_llm

    mock_clarify_llm = MagicMock()
    mock_clarify_struct = MagicMock()
    from clarification import ClarificationOutput

    mock_clarify_struct.invoke.return_value = ClarificationOutput(
        can_resolve=False,
        clarification_question=clarifying_question,
    )
    mock_clarify_llm.with_structured_output.return_value = mock_clarify_struct

    config = {"configurable": {"thread_id": str(uuid4())}}

    with (
        patch("classifier.classifier.default_llm", mock_classifier_llm),
        patch("clarification.engine.default_llm", mock_clarify_llm),
    ):
        result = agent.invoke({"question": question}, config=config)

    assert result["answer"] == clarifying_question
    assert result.get("sql_query") is None
    assert result.get("sql_output") is None


def test_agent_routes_to_out_of_scope_query():
    """Test agent routes out_of_scope_query to handle_out_of_scope_query with fallback message."""
    question = "What is the capital of France?"

    mock_classifier_llm = MagicMock()
    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.return_value = QueryIntent(intent="out_of_scope_query")
    mock_classifier_llm.with_structured_output.return_value = mock_structured_llm

    config = {"configurable": {"thread_id": str(uuid4())}}

    with patch("classifier.classifier.default_llm", mock_classifier_llm):
        result = agent.invoke({"question": question}, config=config)

    assert result["intent"] == "out_of_scope_query"
    assert result["answer"] == OUT_OF_SCOPE_FALLBACK_MESSAGE
    assert result.get("sql_query") is None
    assert result.get("sql_output") is None


def test_agent_routes_to_data_query(run_agent):
    """Test agent routes data_query into existing text-to-sql execution pipeline."""
    question = "List all customer names."
    sql = "SELECT name FROM customers;"
    expected_answer = "Here are the customer names: Alice, Bob, Charlie."

    result = run_agent(
        question=question,
        generated_sql=sql,
        final_answer=expected_answer,
        intent="data_query",
    )

    assert result["intent"] == "data_query"
    assert result["is_valid"] is True
    assert result["sql_query"] == sql
    assert result["answer"] == expected_answer
    assert result["sql_output"] is not None


def test_metadata_formatter_direct():
    """Test format_meta_answer function directly with mocked model."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="Tables: customers, orders")

    answer = format_meta_answer(
        question="What tables exist?",
        schema="CREATE TABLE customers (...);",
        model=mock_llm,
    )
    assert answer == "Tables: customers, orders"
    mock_llm.invoke.assert_called_once()


def test_live_intent_classification():
    """End-to-end integration test with live LLM checking classification accuracy."""
    assert classify_query_intent("Show top 5 products by price") == "data_query"
    assert (
        classify_query_intent("What columns are in the orders table?")
        == "metadata_query"
    )
    assert (
        classify_query_intent("What is the weather like in Tokyo today?")
        == "out_of_scope_query"
    )
    assert classify_query_intent("huh?") == "ambiguous_query"
