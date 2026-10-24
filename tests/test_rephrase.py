import asyncio

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.messaging.providers.base import ProviderError
from app.messaging.service import (
    RephraseService,
    get_bedrock_rephrase_service,
    get_rephrase_service,
)

PAYLOAD = {"message": "i wil com back soon", "member_id": "1", "workspace_id": "2"}


class FakeProvider:
    def __init__(self, result: str | Exception) -> None:
        self._result = result
        self.calls: list[dict] = []

    async def complete_json(self, system, user, schema, max_tokens) -> str:
        self.calls.append(
            {"system": system, "user": user, "schema": schema, "max_tokens": max_tokens}
        )
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def _service(content: str | Exception) -> RephraseService:
    return RephraseService(FakeProvider(content))


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


V1 = "/message/rephrase"  # OpenAI
V2 = "/v2/message/rephrase"  # Bedrock
DEPENDENCY = {V1: get_rephrase_service, V2: get_bedrock_rephrase_service}

both_versions = pytest.mark.parametrize("path", [V1, V2], ids=["v1", "v2"])


def _use(service: RephraseService, path: str) -> None:
    app.dependency_overrides[DEPENDENCY[path]] = lambda: service


def test_healthcheck(client):
    assert client.get("/healthcheck").json() == {"status": "ok"}


@both_versions
def test_rephrase_returns_suggestions(client, path):
    _use(_service('{"suggestions": ["I will be back soon.", "Back shortly!"]}'), path)
    response = client.post(path, json=PAYLOAD)
    assert response.status_code == 200
    assert response.json() == {"data": ["I will be back soon.", "Back shortly!"]}


@both_versions
def test_rephrase_drops_incomplete_sentences(client, path):
    _use(_service('{"suggestions": ["I will be back soon.", "Back in a bit"]}'), path)
    assert client.post(path, json=PAYLOAD).json() == {"data": ["I will be back soon."]}


@both_versions
def test_rephrase_keeps_sentences_ending_in_closing_quote(client, path):
    _use(
        _service('{"suggestions": ["He said \\"okay.\\"", "She left (quickly!)", "No end"]}'), path
    )
    assert client.post(path, json=PAYLOAD).json() == {
        "data": ['He said "okay."', "She left (quickly!)"]
    }


@both_versions
def test_rephrase_handles_unparseable_output(client, path):
    _use(_service("not json"), path)
    assert client.post(path, json=PAYLOAD).json() == {"data": []}


@both_versions
def test_provider_failure_returns_502(client, path):
    _use(_service(ProviderError("boom")), path)
    response = client.post(path, json=PAYLOAD)
    assert response.status_code == 502
    assert response.json() == {"detail": "AI provider unavailable"}


def test_service_passes_user_message_to_provider():
    provider = FakeProvider('{"suggestions": []}')
    asyncio.run(RephraseService(provider).rephrase("hello there"))
    call = provider.calls[0]
    assert call["user"] == "hello there"
    assert call["system"]
    assert call["schema"]["required"] == ["suggestions"]
    assert call["max_tokens"] > 0


@both_versions
@pytest.mark.parametrize("bad", [{"message": "hi"}, {**PAYLOAD, "message": ""}])
def test_rephrase_rejects_invalid_payload(client, path, bad):
    assert client.post(path, json=bad).status_code == 422


def test_versions_use_different_providers(client):
    openai_fake, bedrock_fake = (
        FakeProvider('{"suggestions": ["One."]}'),
        FakeProvider('{"suggestions": ["Two."]}'),
    )
    app.dependency_overrides[get_rephrase_service] = lambda: RephraseService(openai_fake)
    app.dependency_overrides[get_bedrock_rephrase_service] = lambda: RephraseService(bedrock_fake)
    assert client.post(V1, json=PAYLOAD).json() == {"data": ["One."]}
    assert client.post(V2, json=PAYLOAD).json() == {"data": ["Two."]}
    assert len(openai_fake.calls) == len(bedrock_fake.calls) == 1
