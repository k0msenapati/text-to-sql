from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

load_dotenv()


def get_llm(
    model: str = "qwen/qwen3.8-27b",
    provider: str = "groq",
    max_tokens: int = 800,
) -> BaseChatModel:
    """Initializes and returns a chat model instance."""
    return init_chat_model(
        model=model,
        model_provider=provider,
        max_tokens=max_tokens,
    )


llm = get_llm()
