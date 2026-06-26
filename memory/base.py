from abc import ABC, abstractmethod


class BaseMemory(ABC):
    @abstractmethod
    def add(self, messages: list[dict], scope_id: str) -> None:
        """Store new messages into memory for a given scope."""

    @abstractmethod
    def search(self, query: str, scope_id: str) -> list[dict]:
        """Retrieve relevant memories for a query within a scope."""

    @abstractmethod
    def get_all(self, scope_id: str) -> list[dict]:
        """Retrieve all memories for a scope (for history window)."""

    @abstractmethod
    def clear(self, scope_id: str) -> None:
        """Delete all memory for a scope."""
