import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.messaging.providers import ProviderError

ENV_KEYS = [
    "AWS_BEARER_TOKEN_BEDROCK",
    "OPEN_AI_SECRET",
    "OPENAI_MODEL",
    "AWS_REGION",
    "BEDROCK_MODEL_ID",
    "LLM_TIMEOUT_SECONDS",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def settings(monkeypatch):
    def make(**env) -> Settings:
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        return Settings(_env_file=None)

    return make


def test_defaults_need_no_credentials(settings):
    s = settings()
    assert s.openai_api_key is None
    assert s.aws_region == "us-east-1"


def test_openai_key_is_secret(settings):
    s = settings(OPEN_AI_SECRET="sk-test-123")
    assert s.openai_api_key.get_secret_value() == "sk-test-123"
    assert "sk-test-123" not in repr(s)


def test_bedrock_settings_from_env(settings):
    s = settings(AWS_REGION="eu-west-1", BEDROCK_MODEL_ID="m.id")
    assert s.aws_region == "eu-west-1"
    assert s.bedrock_model_id == "m.id"


def test_build_openai_provider(settings):
    from app.messaging.providers import build_openai_provider
    from app.messaging.providers.openai import OpenAIProvider

    provider = build_openai_provider(settings(OPEN_AI_SECRET="k", LLM_TIMEOUT_SECONDS="5"))
    assert isinstance(provider, OpenAIProvider)
    assert provider._client.timeout == 5.0


def test_build_openai_provider_without_key_is_provider_error(settings):
    from app.messaging.providers import build_openai_provider

    with pytest.raises(ProviderError):
        build_openai_provider(settings())


def test_build_bedrock_provider_needs_no_openai_key(settings):
    from app.messaging.providers import build_bedrock_provider
    from app.messaging.providers.bedrock import BedrockProvider

    provider = build_bedrock_provider(settings(BEDROCK_MODEL_ID="m.id"))
    assert isinstance(provider, BedrockProvider)


def test_app_startup_fails_fast_on_invalid_config(monkeypatch):
    from app.config import get_settings
    from app.main import app

    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "0")
    monkeypatch.chdir("/")  # no .env to pick up
    get_settings.cache_clear()
    try:
        with pytest.raises(ValidationError), TestClient(app):
            pass
    finally:
        get_settings.cache_clear()


def test_v1_without_openai_key_returns_502(monkeypatch):
    from app.config import get_settings
    from app.main import app
    from app.messaging.providers import get_bedrock_provider, get_openai_provider

    monkeypatch.chdir("/")
    for fn in (get_settings, get_openai_provider, get_bedrock_provider):
        fn.cache_clear()
    try:
        with TestClient(app) as client:
            payload = {"message": "hi there", "member_id": "1", "workspace_id": "2"}
            r = client.post("/message/rephrase", json=payload)
            assert r.status_code == 502
            assert r.json() == {"detail": "AI provider unavailable"}
    finally:
        for fn in (get_settings, get_openai_provider, get_bedrock_provider):
            fn.cache_clear()


def test_bedrock_api_key_is_passed_to_boto3_environment(settings, monkeypatch):
    import os

    from app.messaging.providers import build_bedrock_provider

    s = settings(AWS_BEARER_TOKEN_BEDROCK="ABSKtest-key")
    assert "ABSKtest-key" not in repr(s)
    build_bedrock_provider(s)
    assert os.environ["AWS_BEARER_TOKEN_BEDROCK"] == "ABSKtest-key"
    monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK")
