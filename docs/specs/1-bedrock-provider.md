# Spec: Amazon Bedrock provider (issue #1)

## Problem
`RephraseService` is coupled to `openai.AsyncOpenAI`. We want the same rephrase task to run on Amazon Bedrock, chosen at runtime.

## Design
- `LLMProvider` protocol: `async complete_json(system, user, schema, max_tokens) -> str`.
- `OpenAIProvider`: existing behavior (strict `json_schema` response format).
- `BedrockProvider`: Converse API, single forced tool whose `inputSchema` is the response schema; returns the tool input as JSON text. Blocking boto3 call runs in `asyncio.to_thread`.
- API versions pick the provider (no env switch): v1 `POST /message/rephrase` uses OpenAI, v2 `POST /v2/message/rephrase` uses Bedrock. Same request/response schema; both can serve at once.
- Settings: `OPEN_AI_SECRET`, `OPENAI_MODEL`, `AWS_REGION`, `BEDROCK_MODEL_ID`, `LLM_TIMEOUT_SECONDS`. AWS credentials via the standard chain only. Each provider is built lazily and cached; v1 without `OPEN_AI_SECRET` returns 502.
- All provider failures become `ProviderError` and surface as HTTP 502.

## Acceptance tests
| Criterion | Test |
|---|---|
| v2 serves the same schema from Bedrock | `tests/test_providers.py` contract suite, `tests/test_rephrase.py` |
| v1 behavior unchanged | `tests/test_rephrase.py`, `tests/test_config.py` |
| Throttling / access denied / malformed output handled | `tests/test_providers.py` error cases |
| Invalid settings fail at startup; v1 without a key returns 502 | `tests/test_config.py` |
| No secrets in logs | reviewer checklist |

## Out of scope
Streaming, per-request provider override, model-quality evals (tracked separately).
