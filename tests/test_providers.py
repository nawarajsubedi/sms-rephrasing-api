import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import openai
import pytest
from botocore.exceptions import BotoCoreError, ClientError

from app.messaging.providers.base import ProviderError
from app.messaging.providers.bedrock import BedrockProvider
from app.messaging.providers.openai import OpenAIProvider

SCHEMA = {
    "type": "object",
    "properties": {"suggestions": {"type": "array", "items": {"type": "string"}}},
    "required": ["suggestions"],
    "additionalProperties": False,
}
RESULT = {"suggestions": ["Hello there."]}


def _openai(mode):
    create = AsyncMock()
    if mode == "ok":
        create.return_value.choices = [MagicMock(message=MagicMock(content=json.dumps(RESULT)))]
    elif mode == "error":
        create.side_effect = openai.APIConnectionError(
            request=httpx.Request("POST", "https://api.openai.com")
        )
    else:  # malformed: no choices
        create.return_value.choices = []
    client = MagicMock()
    client.chat.completions.create = create
    return OpenAIProvider(client, "test-model"), create


def _bedrock(mode):
    converse = MagicMock()
    if mode == "ok":
        converse.return_value = {
            "output": {"message": {"content": [{"toolUse": {"name": "x", "input": RESULT}}]}}
        }
    elif mode == "error":
        converse.side_effect = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "slow"}}, "Converse"
        )
    elif mode == "botocore":
        converse.side_effect = BotoCoreError()
    else:  # malformed: no toolUse block
        converse.return_value = {"output": {"message": {"content": [{"text": "hi"}]}}}
    client = MagicMock()
    client.converse = converse
    return BedrockProvider(client, "test-model-id"), converse


FACTORIES = {"openai": _openai, "bedrock": _bedrock}


def _call(provider):
    return asyncio.run(provider.complete_json("sys", "user msg", SCHEMA, 123))


@pytest.mark.parametrize("name", FACTORIES)
def test_success_returns_json_string(name):
    provider, _ = FACTORIES[name]("ok")
    assert json.loads(_call(provider)) == RESULT


@pytest.mark.parametrize("name", FACTORIES)
def test_upstream_error_becomes_provider_error(name):
    provider, _ = FACTORIES[name]("error")
    with pytest.raises(ProviderError):
        _call(provider)


@pytest.mark.parametrize("name", FACTORIES)
def test_malformed_output_becomes_provider_error(name):
    provider, _ = FACTORIES[name]("malformed")
    with pytest.raises(ProviderError):
        _call(provider)


def test_bedrock_botocore_error_becomes_provider_error():
    provider, _ = _bedrock("botocore")
    with pytest.raises(ProviderError):
        _call(provider)


@pytest.mark.parametrize(
    "response",
    [
        {
            "stopReason": "max_tokens",
            "output": {"message": {"content": [{"toolUse": {"input": {}}}]}},
        },
        {"output": {"message": {"content": [{"toolUse": {"name": "x"}}]}}},
    ],
    ids=["truncated", "missing-input"],
)
def test_bedrock_truncated_or_empty_tool_use_becomes_provider_error(response):
    provider, converse = _bedrock("ok")
    converse.return_value = response
    with pytest.raises(ProviderError):
        _call(provider)


def test_bedrock_request_shape():
    provider, converse = _bedrock("ok")
    _call(provider)
    kwargs = converse.call_args.kwargs
    assert kwargs["modelId"] == "test-model-id"
    assert kwargs["inferenceConfig"]["maxTokens"] == 123
    tools = kwargs["toolConfig"]["tools"]
    assert len(tools) == 1
    spec = tools[0]["toolSpec"]
    assert spec["inputSchema"]["json"] == SCHEMA
    assert kwargs["toolConfig"]["toolChoice"] == {"tool": {"name": spec["name"]}}
    assert "sys" in json.dumps(kwargs["system"])
    assert "user msg" in json.dumps(kwargs["messages"])


def test_openai_request_shape():
    provider, create = _openai("ok")
    _call(provider)
    kwargs = create.call_args.kwargs
    assert kwargs["model"] == "test-model"
    fmt = kwargs["response_format"]
    assert fmt["type"] == "json_schema"
    assert fmt["json_schema"]["strict"] is True
    assert fmt["json_schema"]["schema"] == SCHEMA
    assert [m["role"] for m in kwargs["messages"]] == ["system", "user"]
