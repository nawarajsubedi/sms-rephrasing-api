from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: SecretStr | None = Field(default=None, alias="OPEN_AI_SECRET")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    # Optional Bedrock API key, read from the environment or .env. Without it, boto3 uses
    # its standard credential chain (env vars, ~/.aws profile, IAM role).
    bedrock_api_key: SecretStr | None = Field(default=None, alias="AWS_BEARER_TOKEN_BEDROCK")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    bedrock_model_id: str = Field(
        default="us.anthropic.claude-haiku-4-5-20251001-v1:0", alias="BEDROCK_MODEL_ID"
    )

    llm_timeout_seconds: float = Field(default=30.0, gt=0, alias="LLM_TIMEOUT_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
