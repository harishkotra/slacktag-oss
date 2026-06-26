from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # Slack
    SLACK_BOT_TOKEN: str
    SLACK_APP_TOKEN: str
    SLACK_SIGNING_SECRET: str

    # LLM
    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_API_KEY: str = "ollama"
    LLM_MODEL: str = "llama3.2"

    # Mem0 managed (free tier at app.mem0.ai)
    MEM0_API_KEY: str

    # Bot behavior
    BOT_NAME: str = "Claude"
    MAX_HISTORY_MESSAGES: int = 20
    SYSTEM_PROMPT: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
