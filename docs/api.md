# API Reference

## What this API does

You send a draft message. The API returns up to three improved versions of it:
spelling and grammar fixed, polite and concise. Use it to power an
"auto-suggest" feature in a chat or SMS app.

```
Draft message  ──►  POST /message/rephrase  ──►  ["Suggestion 1.", "Suggestion 2."]
```

There are two versions with the same request and response. **v1** is backed by
OpenAI, **v2** by Amazon Bedrock.

## Endpoints

### `POST /message/rephrase` (v1, OpenAI) and `POST /v2/message/rephrase` (v2, Bedrock)

**Request body (JSON)**

| Field          | Type   | Required | Notes                       |
|----------------|--------|----------|-----------------------------|
| `message`      | string | yes      | The draft text, 1–500 chars |
| `member_id`    | string | yes      | Who is writing              |
| `workspace_id` | string | yes      | Which workspace they are in |

**Example**

```bash
curl -X POST http://127.0.0.1:8000/message/rephrase \
  -H "Content-Type: application/json" \
  -d '{"message": "i wil com back soon", "member_id": "1", "workspace_id": "2"}'
```

**Response `200`**

```json
{ "data": ["I will be back soon.", "I'll return shortly.", "Back soon!"] }
```

`data` may contain fewer than three items, or be empty, if the model's answer
could not be used. Incomplete sentences are never returned.

**Errors**

| Status | Meaning                                              |
|--------|------------------------------------------------------|
| `422`  | Invalid request (missing field, empty/too-long text) |
| `502`  | "AI provider unavailable": the provider (OpenAI or Bedrock) failed or is unreachable (also v1 without `OPEN_AI_SECRET`) |

### `GET /healthcheck`

Returns `{"status": "ok"}`. Use it for uptime checks.

## Configuration

| Variable           | Required         | Default       | Purpose                           |
|--------------------|------------------|---------------|-----------------------------------|
| `OPEN_AI_SECRET`   | v1 only          | —             | OpenAI API key (v1 returns 502 without it) |
| `OPENAI_MODEL`     | no (v1 only)     | `gpt-4o-mini` | OpenAI model                      |
| `LLM_TIMEOUT_SECONDS` | no            | `30`          | Provider connect/read timeout     |
| `AWS_REGION`       | no (v2 only)     | `us-east-1`  | Region where model access is on   |
| `BEDROCK_MODEL_ID` | no (v2 only)     | Claude Haiku profile | Bedrock model or inference profile |

For Bedrock, AWS credentials come from the standard credential chain
(environment variables, `~/.aws` profile, or IAM role) and are not read from
`.env` by the app. The identity needs `bedrock:InvokeModel`, and model access
must be enabled in the region. See the [README](../README.md#configuration).

## Interactive docs

When the server is running, open `/docs` for a Swagger UI where you can try
the endpoint from your browser.
