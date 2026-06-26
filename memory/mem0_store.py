from mem0 import MemoryClient
from config.settings import settings


def get_mem0_client() -> MemoryClient:
    return MemoryClient(api_key=settings.MEM0_API_KEY)
