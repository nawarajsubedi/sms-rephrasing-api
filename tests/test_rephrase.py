from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.messaging import service

client = TestClient(app)
PAYLOAD = {"message": "i wil com back soon", "member_id": "1", "workspace_id": "2"}


def _fake_openai(content: str) -> MagicMock:
    reply = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
    fake = MagicMock()
    fake.chat.completions.create.return_value = reply
    return fake


def test_healthcheck():
    assert client.get("/healthcheck").json() == {"status": "ok"}


def test_rephrase_returns_suggestions():
    fake = _fake_openai('["I will be back soon.", "Back shortly!"]')
    with patch.object(service, "_client", return_value=fake):
        response = client.post("/message/rephrase", json=PAYLOAD)
    assert response.status_code == 200
    assert response.json() == {"data": ["I will be back soon.", "Back shortly!"]}


def test_rephrase_drops_truncated_suggestion():
    fake = _fake_openai('["I will be back soon.", "Back in a bit')
    with patch.object(service, "_client", return_value=fake):
        response = client.post("/message/rephrase", json=PAYLOAD)
    assert response.json() == {"data": ["I will be back soon."]}


def test_rephrase_handles_unparseable_output():
    fake = _fake_openai("Sorry, I can't help with that")
    with patch.object(service, "_client", return_value=fake):
        response = client.post("/message/rephrase", json=PAYLOAD)
    assert response.json() == {"data": []}


def test_rephrase_validates_payload():
    assert client.post("/message/rephrase", json={"message": "hi"}).status_code == 422


@pytest.mark.parametrize("text", ["", "[]"])
def test_parse_empty(text):
    assert service._parse_suggestions(text) == []
