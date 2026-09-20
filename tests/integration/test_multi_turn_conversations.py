from uuid import uuid4
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from text_to_sql.graph import agent


def test_valuable_customer_and_followup_conversation():
    """
    End-to-end integration test verifying the multi-turn scenario:
    Turn 1: 'which customer is most valuable?' -> Identifies Bob Jones.
    Turn 2: 'what was amount spent by Bob?' -> Resolves Bob from context and calculates spending ($280.49).
    Turn 3: 'What tables exist in the database?' -> Answers metadata query with clean state (no SQL query leakage).
    """
    thread_id = f"multi-turn-test-{str(uuid4())}"
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    # Turn 1: Most valuable customer
    res1 = agent.invoke(
        {
            "question": "which customer is most valuable?",
            "messages": [HumanMessage(content="which customer is most valuable?")],
        },
        config=config,
    )
    assert res1["intent"] == "data_query"
    assert res1.get("sql_query") is not None
    assert "Bob Jones" in (res1.get("answer") or "")

    # Turn 2: Conversational follow-up using first name 'Bob'
    res2 = agent.invoke(
        {
            "question": "what was amount spent by Bob?",
            "messages": [HumanMessage(content="what was amount spent by Bob?")],
        },
        config=config,
    )
    assert res2["intent"] == "data_query"
    assert res2.get("sql_query") is not None
    # Verify the SQL query executed and returned Bob Jones's spending (280.49)
    assert "280.49" in (res2.get("answer") or "") or "280.49" in (
        res2.get("sql_output") or ""
    )

    # Turn 3: Metadata query on the SAME thread_id
    res3 = agent.invoke(
        {
            "question": "What tables exist in the database?",
            "messages": [HumanMessage(content="What tables exist in the database?")],
        },
        config=config,
    )
    assert res3["intent"] == "metadata_query"
    # State hygiene: sql_query and sql_output must be None on metadata queries
    assert res3.get("sql_query") is None
    assert res3.get("sql_output") is None
    assert "customers" in (res3.get("answer") or "").lower()


def test_pronoun_followup_conversation():
    """
    Test multi-turn query using pronouns:
    Turn 1: 'Show customers from Canada' -> Identifies Canadian customers.
    Turn 2: 'What did they buy?' -> Resolves 'they' to Canadian customers and executes query.
    """
    thread_id = f"multi-turn-pronoun-{str(uuid4())}"
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    res1 = agent.invoke(
        {
            "question": "Show customers from Canada",
            "messages": [HumanMessage(content="Show customers from Canada")],
        },
        config=config,
    )
    assert res1["intent"] == "data_query"

    res2 = agent.invoke(
        {
            "question": "What did they buy?",
            "messages": [HumanMessage(content="What did they buy?")],
        },
        config=config,
    )
    assert res2.get("answer") is not None
    assert len(res2.get("messages") or []) >= 4
