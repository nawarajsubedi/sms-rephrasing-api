# API Reference

## What this API does

You send a draft message. The API returns up to three improved versions of it:
spelling and grammar fixed, polite and concise. Use it to power an
"auto-suggest" feature in a chat or SMS app.

```
Draft message  ──►  POST /message/rephrase  ──►  ["Suggestion 1.", "Suggestion 2."]
```

## Endpoints

### `POST /message/rephrase`

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
| `502`  | The AI provider (OpenAI) failed or is unreachable    |

### `GET /healthcheck`

Returns `{"status": "ok"}`. Use it for uptime checks.

## Configuration

| Variable        | Required | Default       | Purpose            |
|-----------------|----------|---------------|--------------------|
| `OPEN_AI_SECRET`| yes      | —             | OpenAI API key     |
| `OPENAI_MODEL`  | no       | `gpt-4o-mini` | Model to use       |

## Interactive docs

When the server is running, open `/docs` for a Swagger UI where you can try
the endpoint from your browser.
