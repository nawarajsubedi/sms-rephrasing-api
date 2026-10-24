import asyncio
import json

from botocore.exceptions import BotoCoreError, ClientError

from app.messaging.providers.base import ProviderError

TOOL_NAME = "return_result"


class BedrockProvider:
    def __init__(self, client, model_id: str) -> None:
        self._client = client
        self._model_id = model_id

    async def complete_json(self, system: str, user: str, schema: dict, max_tokens: int) -> str:
        try:
            response = await asyncio.to_thread(
                self._client.converse,
                modelId=self._model_id,
                system=[{"text": system}],
                messages=[{"role": "user", "content": [{"text": user}]}],
                inferenceConfig={"maxTokens": max_tokens},
                toolConfig={
                    "tools": [
                        {
                            "toolSpec": {
                                "name": TOOL_NAME,
                                "description": "Return the result as structured JSON.",
                                "inputSchema": {"json": schema},
                            }
                        }
                    ],
                    "toolChoice": {"tool": {"name": TOOL_NAME}},
                },
            )
        except (ClientError, BotoCoreError) as exc:
            raise ProviderError("Bedrock request failed") from exc

        if response.get("stopReason") == "max_tokens":
            raise ProviderError("Bedrock output was truncated (max_tokens)")

        try:
            blocks = response["output"]["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise ProviderError("Bedrock response had no message content") from exc
        for block in blocks:
            tool_use = block.get("toolUse") if isinstance(block, dict) else None
            if tool_use is not None:
                if "input" not in tool_use:
                    raise ProviderError("Bedrock toolUse block had no input")
                return json.dumps(tool_use["input"])
        raise ProviderError("Bedrock response contained no toolUse block")
