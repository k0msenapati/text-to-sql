from unittest.mock import MagicMock, patch
from uuid import uuid4
from langchain_core.messages import AIMessage, HumanMessage

from text_to_sql.graph import agent
from text_to_sql.nodes import (
    ClarificationOutput,
    QueryIntent,
    format_clarification_response,
    format_message_history,
    resolve_or_clarify_query,
)


def test_format_message_history():
    messages = [
        HumanMessage(content="Show customers in Canada"),
        AIMessage(content="Found Bob and Alice in Canada."),
        HumanMessage(content="What did they buy?"),
    ]
    formatted = format_message_history(messages)
    assert "User: Show customers in Canada" in formatted
    assert "Assistant: Found Bob and Alice in Canada." in formatted
    # The last message is the current turn, so it is excluded from past history
    assert "What did they buy?" not in formatted


def test_resolve_or_clarify_query_resolves():
    mock_llm = MagicMock()
    mock_struct = MagicMock()
    mock_struct.invoke.return_value = ClarificationOutput(
        can_resolve=True,
        resolved_query="Show orders for customers located in Canada.",
    )
    mock_llm.with_structured_output.return_value = mock_struct

    res = resolve_or_clarify_query(
        question="What did they buy?",
        messages=[
            HumanMessage(content="Show customers in Canada"),
            AIMessage(content="Found Bob and Alice in Canada."),
        ],
        schema="CREATE TABLE customers (...);",
        model=mock_llm,
    )
    assert res.can_resolve is True
    assert res.resolved_query == "Show orders for customers located in Canada."


def test_resolve_or_clarify_query_clarifies():
    mock_llm = MagicMock()
    mock_struct = MagicMock()
    mock_struct.invoke.return_value = ClarificationOutput(
        can_resolve=False,
        clarification_question="Could you please clarify what you would like to view?",
        options=["Products by revenue", "Products by rating"],
    )
    mock_llm.with_structured_output.return_value = mock_struct

    res = resolve_or_clarify_query(
        question="Show top products",
        messages=[],
        schema="CREATE TABLE products (...);",
        model=mock_llm,
    )
    assert res.can_resolve is False
    assert len(res.options) == 2


def test_format_clarification_response():
    output = ClarificationOutput(
        can_resolve=False,
        clarification_question="What would you like to see?",
        options=["List all products", "List all orders"],
    )
    msg = format_clarification_response(output)
    assert "What would you like to see?" in msg
    assert "1. List all products" in msg
    assert "2. List all orders" in msg


def test_agent_resolves_ambiguous_query_via_history():
    """
    End-to-end multi-turn test:
    Turn 1: User asks data query.
    Turn 2: User asks ambiguous follow-up 'What did they buy?'.
    Agent uses clarification_engine to rewrite query using history, then runs SQL pipeline!
    """
    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    mock_classifier = MagicMock()
    mock_class_struct = MagicMock()
    # Turn 1 is data_query, Turn 2 is ambiguous_query
    mock_class_struct.invoke.side_effect = [
        QueryIntent(intent="data_query"),
        QueryIntent(intent="ambiguous_query"),
    ]
    mock_classifier.with_structured_output.return_value = mock_class_struct

    mock_clarifier = MagicMock()
    mock_clar_struct = MagicMock()
    mock_clar_struct.invoke.return_value = ClarificationOutput(
        can_resolve=True,
        resolved_query="SELECT * FROM orders WHERE customer_id IN (SELECT customer_id FROM customers WHERE country = 'Canada');",
    )
    mock_clarifier.with_structured_output.return_value = mock_clar_struct

    mock_generator = MagicMock()
    mock_generator.invoke.side_effect = [
        AIMessage(content="SELECT * FROM customers WHERE country = 'Canada';"),
        AIMessage(content="SELECT * FROM orders WHERE customer_id IN (2, 7);"),
    ]

    mock_formatter = MagicMock()
    mock_formatter.invoke.side_effect = [
        AIMessage(content="Customers in Canada: Bob, George."),
        AIMessage(content="Orders bought by Canadian customers: Order 102, Order 105."),
    ]

    with (
        patch("text_to_sql.nodes.classify.default_llm", mock_classifier),
        patch("text_to_sql.nodes.clarify.default_llm", mock_clarifier),
        patch("text_to_sql.nodes.generate_sql.default_llm", mock_generator),
        patch("text_to_sql.nodes.format_answer.default_llm", mock_formatter),
    ):
        # Turn 1
        res1 = agent.invoke(
            {
                "question": "Show customers in Canada",
                "messages": [HumanMessage(content="Show customers in Canada")],
            },
            config=config,
        )
        assert res1["answer"] == "Customers in Canada: Bob, George."

        # Turn 2: Ambiguous follow-up
        res2 = agent.invoke(
            {
                "question": "What did they buy?",
                "messages": [HumanMessage(content="What did they buy?")],
            },
            config=config,
        )
        assert (
            res2["answer"]
            == "Orders bought by Canadian customers: Order 102, Order 105."
        )
        assert len(res2["messages"]) >= 4


def test_resolve_entity_correction_from_history():
    """Verify that providing an entity correction like 'Bob Jones' resolves to a full query."""
    mock_llm = MagicMock()
    mock_struct = MagicMock()
    mock_struct.invoke.return_value = ClarificationOutput(
        can_resolve=True,
        resolved_query="What was the total amount spent by Bob Jones?",
    )
    mock_llm.with_structured_output.return_value = mock_struct

    res = resolve_or_clarify_query(
        question="Bob Jones",
        messages=[
            HumanMessage(content="what was amount spent by Bob?"),
            AIMessage(content="no records found for Bob"),
        ],
        schema="CREATE TABLE customers (...);",
        model=mock_llm,
    )
    assert res.can_resolve is True
    assert res.resolved_query == "What was the total amount spent by Bob Jones?"
