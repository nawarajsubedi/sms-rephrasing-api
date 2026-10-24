import os
from functools import lru_cache

from botocore.exceptions import BotoCoreError

from app.config import Settings, get_settings
from app.messaging.providers.base import LLMProvider, ProviderError

__all__ = [
    "LLMProvider",
    "ProviderError",
    "build_bedrock_provider",
    "build_openai_provider",
    "get_bedrock_provider",
    "get_openai_provider",
]


def build_openai_provider(settings: Settings) -> LLMProvider:
    import openai

    from app.messaging.providers.openai import OpenAIProvider

    if not settings.openai_api_key:
        raise ProviderError("OPEN_AI_SECRET is not configured")
    client = openai.AsyncOpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=settings.llm_timeout_seconds,
    )
    return OpenAIProvider(client, settings.openai_model)


def build_bedrock_provider(settings: Settings) -> LLMProvider:
    import boto3
    from botocore.config import Config

    from app.messaging.providers.bedrock import BedrockProvider

    if settings.bedrock_api_key:
        # boto3 reads a Bedrock API key only from the process environment, not from .env.
        os.environ.setdefault(
            "AWS_BEARER_TOKEN_BEDROCK", settings.bedrock_api_key.get_secret_value()
        )

    config = Config(
        connect_timeout=settings.llm_timeout_seconds,
        read_timeout=settings.llm_timeout_seconds,
        retries={"max_attempts": 2, "mode": "standard"},
    )
    try:
        client = boto3.client("bedrock-runtime", region_name=settings.aws_region, config=config)
    except BotoCoreError as exc:
        raise ProviderError("Could not create Bedrock client") from exc
    return BedrockProvider(client, settings.bedrock_model_id)


@lru_cache
def get_openai_provider() -> LLMProvider:
    """One OpenAI provider (and SDK client) per process."""
    return build_openai_provider(get_settings())


@lru_cache
def get_bedrock_provider() -> LLMProvider:
    """One Bedrock provider (and SDK client) per process."""
    return build_bedrock_provider(get_settings())
