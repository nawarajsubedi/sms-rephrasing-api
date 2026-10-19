---
name: review-standards
description: Code review checklist for this project (FastAPI + OpenAI services). Use when reviewing a PR, branch diff or your own changes before committing.
---

# Review standards

Check in this order. Report only what you verified by reading the code.

## 1. Correctness
- Logic errors, unhandled None/empty input, wrong error handling.
- Async misuse: blocking calls inside `async def`, missing `await`.
- Behavior changes not reflected in callers.

## 2. Security
- No secrets in code, logs or committed files; `.env` stays ignored, `.env.example` has placeholders only.
- All request input validated by Pydantic schemas (length limits, types).
- Error responses don't leak provider or internal details (e.g. 502 "AI provider unavailable").

## 3. API contract and docs
- Route, schema or config changes are reflected in `README.md`, `docs/api.md` and `.env.example`.
- Response models declared on routes; status codes are accurate.

## 4. Tests
- New behavior and failure paths are covered.
- OpenAI is mocked via dependency overrides; tests never call the real API.
- `ruff check .` and `pytest` both pass.

## 5. Maintainability
- Settings come from `app/config.py`, not `os.environ` scattered in code.
- Dependencies injected with `Depends`, not constructed inline.
- No dead code, duplicated logic or comments that restate the code.

## 6. LLM calls
- `max_tokens` set and a timeout configured.
- Structured output (`response_format`) parsed defensively; malformed output handled.
- User text is treated as data, not instructions (prompt-injection exposure noted).
- Model name comes from settings, not hard-coded.
