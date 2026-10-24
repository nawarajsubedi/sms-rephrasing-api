# SMS Rephrasing API

FastAPI service that rephrases draft messages with an LLM. Providers (OpenAI, Amazon Bedrock) sit behind the `LLMProvider` protocol in `app/messaging/providers/`.

## Commands

- Install: `pip install -r requirements-dev.txt`
- Test: `pytest`
- Lint: `ruff check .`
- Run: `fastapi dev app/main.py`

CI runs `ruff check .` and `pytest`; both must pass before a PR.

## AI-first workflow

1. **Issue first.** Every change starts as a GitHub issue with acceptance criteria. Branch name: `feature/<issue#>-<slug>`.
2. **Spec before code.** Non-trivial changes get a short spec in `docs/specs/<issue#>-<slug>.md` (problem, design, interfaces, acceptance tests). Agents code against the spec, not against each other.
3. **Parallel agents with disjoint file ownership.** Use `.claude/agents/`: `provider-implementer` (app/), `provider-test-writer` (tests/), `provider-docs-writer` (docs, README, examples). Define the interface contract first; never let two agents edit the same file.
4. **Tests encode acceptance criteria.** Every criterion in the issue maps to a test. Mock all LLM and AWS clients; tests never touch the network or real credentials.
5. **Independent review.** Run the `pr-reviewer` agent (uses the `review-standards` skill) before opening a PR. Fix blocking findings, then re-run.
6. **Human gate.** Commit, push and PR creation happen only on explicit request. The PR links the issue (`Closes #N`).

## Conventions

- Match surrounding code style; ruff config is in `pyproject.toml`.
- Secrets come from env/`.env` (never committed). AWS credentials use the standard credential chain only; never add secret fields for them and never log keys or request bodies.
- v1 (`/message/rephrase`) stays on OpenAI so existing behavior does not change; v2 (`/v2/message/rephrase`) uses Bedrock. The API version picks the provider, not an env var.
- Provider SDK errors are wrapped in `ProviderError`; the API returns 502 `{"detail": "AI provider unavailable"}`.
