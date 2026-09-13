import logging
import os
from uuid import uuid4

from agent import agent

# Clean, minimal log format
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

config = {"configurable": {"thread_id": str(uuid4())}}


def print_graph():
    print("\n" + "=" * 45)
    print("AGENT WORKFLOW GRAPH")
    print("=" * 45)

    print(agent.get_graph().draw_ascii())


def main():
    while True:
        try:
            user_input = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input or user_input.lower() in ["exit", "quit"]:
            break

        if user_input.lower() == "graph":
            print_graph()
            continue

        try:
            response = agent.invoke({"question": user_input}, config=config)  # type: ignore
            logger.info("Agent run complete\n")

            print(response["answer"])

        except Exception as e:
            logger.error("Agent run failed: %s", e)
            raise


if __name__ == "__main__":
    main()
