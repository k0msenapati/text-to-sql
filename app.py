from typing import cast
from uuid import uuid4

import chainlit as cl
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from text_to_sql.graph import agent
from text_to_sql.state import AgentState


@cl.set_starters  # type: ignore
async def set_starters():
    return [
        cl.Starter(
            label="Customers in Canada",
            message="Show customers from Canada with their email and country",
        ),
        cl.Starter(
            label="Top Selling Products",
            message="Which products have the highest total quantity sold?",
        ),
        cl.Starter(
            label="Average Product Rating",
            message="What is the average rating for each product based on reviews?",
        ),
        cl.Starter(
            label="Ambiguous Query Test",
            message="Show me recent sales",
        ),
    ]


@cl.on_chat_start
async def start_chat():
    cl.user_session.set("thread_id", str(uuid4()))
    await cl.Message(
        content=(
            "👋 **Welcome to the Text-to-SQL Assistant!**\n\n"
            "Ask any natural language questions to query data, inspect database schemas, "
            "or get help with ambiguous requests. Select a starter prompt below or type your question!"
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    thread_id = cast(str, cl.user_session.get("thread_id"))
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    async with cl.Step(name="Thinking & Intent Analysis", type="run") as run_step:
        try:
            input_state: AgentState = {
                "question": message.content,
                "messages": [HumanMessage(content=message.content)],
            }
            response: AgentState = cast(
                AgentState,
                await agent.ainvoke(
                    input_state,
                    config=config,
                ),
            )
            intent = response.get("intent", "data_query")
            run_step.output = f"Identified Intent: `{intent}`"
        except Exception as e:
            run_step.output = f"Failed with error: {e}"
            await cl.Message(content=f"❌ An error occurred: {e}").send()
            return

    sql_query = response.get("sql_query")
    intent = response.get("intent")
    if intent == "data_query" and sql_query:
        async with cl.Step(name="Executed SQL Query", type="tool") as sql_step:
            sql_step.output = f"```sql\n{sql_query}\n```"

    answer = response.get("answer") or "No answer returned."
    await cl.Message(content=answer).send()
