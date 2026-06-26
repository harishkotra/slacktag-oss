from langchain_openai import ChatOpenAI
from config.settings import settings


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
        temperature=0.7,
        streaming=True,
    )
