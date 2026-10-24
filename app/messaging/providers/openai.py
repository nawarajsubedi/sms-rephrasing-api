import openai

from app.messaging.providers.base import ProviderError


class OpenAIProvider:
    def __init__(self, client: openai.AsyncOpenAI, model: str) -> None:
        self._client = client
        self._model = model

    async def complete_json(self, system: str, user: str, schema: dict, max_tokens: int) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "suggestions", "strict": True, "schema": schema},
                },
                max_tokens=max_tokens,
            )
        except openai.OpenAIError as exc:
            raise ProviderError("OpenAI request failed") from exc
        try:
            return response.choices[0].message.content or ""
        except (IndexError, AttributeError, TypeError) as exc:
            raise ProviderError("OpenAI returned an unexpected response") from exc
