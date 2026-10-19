import json
import logging

import openai
from fastapi import Depends

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You rephrase a draft message. Fix spelling and grammar, keep it polite and "
    "concise, and give up to three alternative suggestions. Each suggestion must "
    "be a complete sentence."
)

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "suggestions",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {"suggestions": {"type": "array", "items": {"type": "string"}}},
            "required": ["suggestions"],
            "additionalProperties": False,
        },
    },
}


class RephraseService:
    def __init__(self, client: openai.AsyncOpenAI, model: str) -> None:
        self._client = client
        self._model = model

    async def rephrase(self, message: str) -> list[str]:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            response_format=RESPONSE_FORMAT,
            max_tokens=200,
        )
        return self._parse(response.choices[0].message.content or "")

    @staticmethod
    def _parse(content: str) -> list[str]:
        try:
            suggestions = json.loads(content)["suggestions"]
        except (json.JSONDecodeError, KeyError, TypeError):
            logger.warning("Unparseable model output: %r", content)
            return []
        return [s for s in suggestions if s.endswith((".", "!", "?"))]


def get_rephrase_service(settings: Settings = Depends(get_settings)) -> RephraseService:
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    return RephraseService(client, settings.openai_model)
