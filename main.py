import logging
import os
from uuid import uuid4
from langchain_core.runnables import RunnableConfig
from langchain.messages import HumanMessage

from agent.agent import agent
from agent.utils import get_graph

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

config: RunnableConfig = {"configurable": {"thread_id": f"conversation-{str(uuid4())}"}}


def main():
    while True:
        try:
            user_input = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input or user_input.lower() in ["exit", "quit"]:
            break

        if user_input.lower() == "graph":
            print("\n" + "=" * 45)
            print("AGENT WORKFLOW GRAPH")
            print("=" * 45)

            print(get_graph(agent))
            continue

        try:
            response = agent.invoke(
                {
                    "question": user_input,
                    "messages": [HumanMessage(content=user_input)],
                },
                config=config,
            )
            logger.info("[main] Agent run complete\n")

            print(response["answer"])

        except Exception as e:
            logger.error("[main] Agent run failed: %s", e)
            raise


if __name__ == "__main__":
    main()
