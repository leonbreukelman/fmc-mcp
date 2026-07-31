# Project Card — fmc-mcp

Local instantiation of `docs/method/METHOD.md`. This is the only method file edited per repo. It may select a globally defined lifecycle mode and add stricter constraints; it may not loosen the global contract.

Generated: 2026-07-02
Last updated: 2026-07-30

## Lifecycle mode

`github-pr`

Mode notes:
All changes land through a focused branch and GitHub pull request. Local verification, independent review, public-boundary scanning, exact-head CI, merge read-back, and post-merge verification are required.

## Protected / frozen paths

- `.github/workflows/**`
- `.github/dependabot.yml`
- `pyproject.toml`
- `uv.lock`
- `.env.example`
- `src/fmc_mcp/config.py`
- `SECURITY.md`

Changes to these paths require explicit scope, regression coverage where applicable, and independent review before merge.

## Gate commands

- `uv lock --check`
- `uv run --extra dev python -m pytest -q`
- `uv run --extra dev python -m pytest --cov=src/fmc_mcp --cov-report=term-missing --cov-fail-under=80 -q`
- `uv run --extra dev ruff check .`
- `uv run --extra dev ruff format --check .`
- `uv run --extra dev python -m mypy src tests`
- `uv run --extra dev pyright`
- `uv run --extra dev pre-commit run --all-files`
- Build the sdist and wheel, then install/import the wheel in a clean environment.
- Export and audit runtime dependencies with no known vulnerabilities.

## CI

Present. `ci.yml` runs the supported-Python test matrix and a required aggregate gate; `codeql.yml` performs code scanning.

## Connector scope

GitHub origin and write-capable CLI authentication are verified. `main` is protected after the repository-refresh merge; the aggregate `CI gate` check is required.

## Secrets / provider contract

No secret values belong in repo docs. Only env-var names may be listed here.

Allowed names: `FMC_HOST`, `FMC_USERNAME`, `FMC_PASSWORD`, `FMC_VERIFY_SSL`, `FMC_DOMAIN_UUID`, `FMC_TIMEOUT`, `FMC_RATE_LIMIT`, `FMC_MAX_CONNECTIONS`, `MCP_TRANSPORT`, `MCP_HOST`, `MCP_PORT`.

## Exit codes

No repo-specific exit-code contract declared yet.

## Escalation wiring

- Claude Code CLI: available
- Grok CLI: available
- Copilot CLI: available
- Fable: use only after explicit preflight; never silently substitute another model.

## Pairing

Implementer: Hermes Agent / delegated coding agent within scope.
Certifier/reviewer: Claude Code Opus by default; Fable only after preflight or explicit Tier-4 escalation.
Verifier: Hermes/Leon flow checks ledger against live evidence.

## Current repo facts

- Repo path: repository root
- Git root: repository root
- Base SHA at install: `25f445806d5221f21d7ac675799db5c30499f1b7`
- Origin: `git@github.com:leonbreukelman/fmc-mcp.git`

## Open decisions

None.
