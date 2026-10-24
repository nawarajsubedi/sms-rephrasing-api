---
name: ai-first-feature
description: End-to-end AI-first workflow for building a feature in this project: GitHub issue, branch, spec, parallel agents, full test run, independent review, then PR. Use when the user asks to implement, build or add a feature or ticket.
---

# AI-first feature workflow

Follow the stages in order. Each stage has an exit check; do not start the next stage until it passes. Report real results, never assumed ones.

## 1. Issue

- Create a GitHub issue with `gh issue create`: summary, motivation, proposed design, acceptance criteria as a checklist, and a work breakdown.
- If `gh` is missing or not logged in, say so and ask the user to run `! gh auth login`. There is no GitHub MCP server here.
- **Exit check:** the issue URL exists.

## 2. Branch

- `git checkout -b feature/<issue#>-<slug>` from an up-to-date `main`. Never work on `main`.
- **Exit check:** `git branch --show-current` shows the new branch.

## 3. Spec

- Write `docs/specs/<issue#>-<slug>.md`: problem, design, interfaces, and a table mapping every acceptance criterion to the test that proves it.
- Fix the interface contract (module names, function signatures, config names, error behavior) here. Agents code against the spec, not against each other.
- **Exit check:** every acceptance criterion has a named test.

## 4. Build with parallel agents

Use agents only for work that splits cleanly. Small or tightly coupled changes are done directly.

- Give each agent **disjoint file ownership** (for example `app/`, `tests/`, `docs/` + `README.md`) and the contract from the spec. Two agents never edit the same file.
- Agents available in `.claude/agents/`: `provider-implementer`, `provider-test-writer`, `provider-docs-writer`, `pr-reviewer`. Otherwise use `general-purpose` with an inline prompt.
- Run independent agents in parallel in the background. Do not poll.
- Agents tell you what they think they did. **Read the diff yourself** and run the checks; an agent's report can be empty or wrong.
- **Exit check:** all agents reported and `git status` shows only expected files.

## 5. Full test run (blocking gate)

Use a clean virtualenv in the scratchpad so missing dependencies show up.

```bash
python3 -m venv <scratchpad>/venv
<scratchpad>/venv/bin/pip install -q -r requirements-dev.txt
<scratchpad>/venv/bin/ruff check .
<scratchpad>/venv/bin/ruff format --check app tests
<scratchpad>/venv/bin/python -m pytest -q
```

- Run the whole suite, never a subset, and never with `-k`, `--deselect`, `-x` or skip flags.
- A failure is fixed in the code, not by weakening or deleting the test. Investigate whether the test or the code is wrong before changing either.
- Mocked tests do not prove an integration works. If `.env` has credentials for the real service, also run a live check (a running server plus requests covering valid input, validation errors and provider failures) and say so. If it cannot be run, record that as untested.
- **Exit check:** lint clean, all tests pass, real counts recorded.

## 6. Independent review

- Run the `pr-reviewer` agent on `git diff main...HEAD` plus untracked files.
- Fix blocking findings, then repeat stage 5. Record deferred non-blocking items for the PR body.
- Compare docs against the code: every env var, default and endpoint named in README and `docs/` must match what the code does.

## 7. Commit and PR

- Never commit `.env`, keys or key-shaped strings. Never print a secret value; when inspecting `.env`, show only key names and use `cut`/`sed` that cannot echo a full line.
- Commit in logical chunks with the attribution trailer from the session's system reminder.
- Hand off to the **`open-pr`** skill, which re-runs the full test gate, pushes, and opens the PR with `Closes #<issue>`.
- Never merge the PR.

## Hard rules

- Do not skip a stage or a gate because the change looks small; say instead which stages you are omitting and why.
- State clearly what was not tested.
- Ask before destructive or outward-facing actions that the user did not request.
