from memory.base import BaseMemory
from memory.mem0_store import get_mem0_client


class DMMemory(BaseMemory):
    def __init__(self):
        self.client = get_mem0_client()

    def scope_id(self, user_id: str) -> str:
        return f"dm:{user_id}"

    def add(self, messages: list[dict], scope_id: str) -> None:
        self.client.add(messages, user_id=scope_id)

    def search(self, query: str, scope_id: str) -> list[dict]:
        return self.client.search(query, user_id=scope_id, limit=10)

    def get_all(self, scope_id: str) -> list[dict]:
        return self.client.get_all(user_id=scope_id)

    def clear(self, scope_id: str) -> None:
        self.client.delete_all(user_id=scope_id)
