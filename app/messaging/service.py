import json
import logging

from fastapi import Depends

from app.messaging.providers import LLMProvider, get_bedrock_provider, get_openai_provider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You rephrase a draft message. Fix spelling and grammar, keep it polite and "
    "concise, and give up to three alternative suggestions. Each suggestion must "
    "be a complete sentence."
)

# A complete sentence may end inside a closing quote or bracket, e.g. He said "okay."
SENTENCE_END = (".", "!", "?")
CLOSING_CHARS = "\"'”’)]}"

SUGGESTIONS_SCHEMA = {
    "type": "object",
    "properties": {"suggestions": {"type": "array", "items": {"type": "string"}}},
    "required": ["suggestions"],
    "additionalProperties": False,
}


class RephraseService:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def rephrase(self, message: str) -> list[str]:
        content = await self._provider.complete_json(
            SYSTEM_PROMPT, message, SUGGESTIONS_SCHEMA, max_tokens=200
        )
        return self._parse(content)

    @staticmethod
    def _parse(content: str) -> list[str]:
        try:
            suggestions = json.loads(content)["suggestions"]
        except (json.JSONDecodeError, KeyError, TypeError):
            logger.warning("Unparseable model output: %r", content)
            return []
        return [s for s in suggestions if s.rstrip(CLOSING_CHARS).endswith(SENTENCE_END)]


def get_rephrase_service(provider: LLMProvider = Depends(get_openai_provider)) -> RephraseService:
    """v1: OpenAI."""
    return RephraseService(provider)


def get_bedrock_rephrase_service(
    provider: LLMProvider = Depends(get_bedrock_provider),
) -> RephraseService:
    """v2: Amazon Bedrock."""
    return RephraseService(provider)
