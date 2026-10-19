from unittest.mock import AsyncMock, MagicMock

import httpx
import openai
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.messaging.service import RephraseService, get_rephrase_service

PAYLOAD = {"message": "i wil com back soon", "member_id": "1", "workspace_id": "2"}


def _service(content: str | Exception) -> RephraseService:
    create = AsyncMock()
    if isinstance(content, Exception):
        create.side_effect = content
    else:
        create.return_value.choices = [MagicMock(message=MagicMock(content=content))]
    client = MagicMock()
    client.chat.completions.create = create
    return RephraseService(client, model="test-model")


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _use(service: RephraseService) -> None:
    app.dependency_overrides[get_rephrase_service] = lambda: service


def test_healthcheck(client):
    assert client.get("/healthcheck").json() == {"status": "ok"}


def test_rephrase_returns_suggestions(client):
    _use(_service('{"suggestions": ["I will be back soon.", "Back shortly!"]}'))
    response = client.post("/message/rephrase", json=PAYLOAD)
    assert response.status_code == 200
    assert response.json() == {"data": ["I will be back soon.", "Back shortly!"]}


def test_rephrase_drops_incomplete_sentences(client):
    _use(_service('{"suggestions": ["I will be back soon.", "Back in a bit"]}'))
    assert client.post("/message/rephrase", json=PAYLOAD).json() == {
        "data": ["I will be back soon."]
    }


def test_rephrase_handles_unparseable_output(client):
    _use(_service("not json"))
    assert client.post("/message/rephrase", json=PAYLOAD).json() == {"data": []}


def test_openai_failure_returns_502(client):
    error = openai.APIConnectionError(request=httpx.Request("POST", "https://api.openai.com"))
    _use(_service(error))
    response = client.post("/message/rephrase", json=PAYLOAD)
    assert response.status_code == 502


@pytest.mark.parametrize("bad", [{"message": "hi"}, {**PAYLOAD, "message": ""}])
def test_rephrase_rejects_invalid_payload(client, bad):
    assert client.post("/message/rephrase", json=bad).status_code == 422
