---
name: open-pr
description: Open a pull request for the current branch in this project. Runs the full test suite and lint first and refuses to open the PR if anything fails. Use when the user asks to open, create or raise a PR.
---

# Open a PR

Invoking this skill is the user's request to push the branch and open a PR. Run the steps in order and stop at the first failure. Never skip or weaken a gate to get the PR open.

## 1. Preconditions

- `git branch --show-current` is not `main`. Branch name should be `feature/<issue#>-<slug>`; take the issue number from it.
- `git status --short` shows no uncommitted changes. If there are any, tell the user and stop; do not commit on their behalf unless they ask.
- An open PR for the branch does not already exist: `gh pr list --head <branch> --state open`.

## 2. Full test run (blocking gate)

Use a clean virtualenv so a missing dependency in `requirements*.txt` shows up. Put it in the scratchpad, not the repo.

```bash
python3 -m venv <scratchpad>/pr-venv
<scratchpad>/pr-venv/bin/pip install -q -r requirements-dev.txt
<scratchpad>/pr-venv/bin/ruff check .
<scratchpad>/pr-venv/bin/ruff format --check app tests
<scratchpad>/pr-venv/bin/python -m pytest -q
```

- Run the **whole** suite, never a subset, and never with `-k`, `--deselect`, `-x` or a skip flag.
- All three must pass. If any fails, report the failing test names and output, and **stop**. Do not push, do not open the PR, and do not edit tests to make them pass.
- Report the real counts (for example "37 passed"). Do not say tests passed without having run them in this turn.
- If the change touches a live integration (Bedrock, OpenAI) and credentials are available in `.env`, also run a short live smoke test and record it. If it could not be run, say so in the PR body.

## 3. Safety checks

- `git check-ignore .env` must confirm `.env` is ignored.
- Search tracked and new files for key-shaped strings (`ABSK...`, `sk-...`, `AKIA...`); stop if any are found.
- Run the `pr-reviewer` agent on the branch diff (`git diff main...HEAD`). Fix blocking findings and re-run the tests (step 2) before continuing. Non-blocking findings go in the PR body.

## 4. Push and open

1. `git push -u origin <branch>`
2. Write the body to a file in the scratchpad using `.github/pull_request_template.md`:
   - First line `Closes #<issue>`.
   - Summary of the change.
   - Spec link under `docs/specs/` if one exists.
   - **Testing**: the exact commands run and real results, plus anything not tested (unchecked boxes).
   - Review outcome and anything deferred.
   - AI-assisted development: agents used and what each owned.
   - Final line: `🤖 Generated with [Claude Code](https://claude.com/claude-code)`
3. `gh pr create --base main --head <branch> --title "<title>" --body-file <file>`
4. `gh pr view --json url,closingIssuesReferences` to confirm the issue link, then `gh pr checks` and report CI status.

## 5. Report

Give the PR URL, the test and lint results with counts, what was not tested, and the CI state. Never merge the PR.
