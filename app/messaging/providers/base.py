from typing import Protocol


class ProviderError(Exception):
    """Raised when an LLM provider call fails."""


class LLMProvider(Protocol):
    async def complete_json(self, system: str, user: str, schema: dict, max_tokens: int) -> str:
        """Return the model's answer as raw JSON text matching `schema`."""
        ...
