# Repository refresh verification

Date: 2026-07-30
Scope: maintenance branch before pull request

## Regression-first proof

The new regressions were run before implementation. The client/resource set and configuration set both failed against the old implementation. The failures covered missing MCP settings validation, non-positive FMC limits, rate accounting, token-header validation, concurrent refresh, HTTP-date retry handling, count-independent pagination, deployment permission denial, and unknown device filters.

## Local deterministic gates

| Gate | Command | Result |
| --- | --- | --- |
| Lock reproducibility | `uv lock --check` | PASS; 82 packages resolved. |
| Frozen development sync | `uv sync --extra dev --frozen` | PASS. |
| Unit suite | `uv run --extra dev python -m pytest -q` | PASS; 54 passed, 1 opt-in live test skipped. |
| Branch coverage | `uv run --extra dev python -m pytest --cov=src/fmc_mcp --cov-report=term-missing --cov-fail-under=80 -q` | PASS; 81.95%. |
| Ruff lint | `uv run --extra dev ruff check .` | PASS. |
| Ruff format | `uv run --extra dev ruff format --check .` | PASS. |
| Strict typing | `uv run --extra dev python -m mypy src tests` | PASS; 13 source/test files. |
| Build Arena typing metric | `uv run --extra dev pyright --outputjson` | PASS; Pyright 1.1.411 analyzed 13 files with zero diagnostics. |
| Repository hooks | `uv run --extra dev pre-commit run --all-files` | PASS. |
| Workflow syntax | actionlint 1.7.12 over `.github/workflows` | PASS. |
| Build | `uv build --out-dir <temporary-directory>` | PASS; one wheel and one source distribution. |
| Clean wheel | install built wheel into a fresh Python 3.12 environment | PASS; package import and MCP registry smoke succeeded with MCP 1.29.0. |
| Runtime audit | export frozen runtime requirements, then `pip-audit` | PASS; no known vulnerabilities. |
| Method scaffold | structural file and `AGENTS.md` load-hook assertions | PASS. |
| Publication boundary | staged secret, absolute-home-path, and private-IP scan | PASS; zero findings. |
| Diff integrity | `git diff --cached --check` | PASS. |

## Explicit boundary

The opt-in real-FMC smoke was not run because no authorized sandbox credential set was supplied to this maintenance flow. No appliance, production, or endpoint certification is claimed. That gate remains:

```bash
FMC_LIVE_TEST=1 uv run --extra dev python -m pytest -q -m live
```

Remote GitHub CI, CodeQL, and the aggregate `CI gate` must pass on the pull request before merge.

## Independent review

The first directory review used the intended Opus model but exhausted its fixed turn budget without a verdict; it was classified as incomplete and not used as evidence. The documented sealed inline/no-tool fallback completed with actual model `claude-opus-4-8` and verdict `ACCEPT`.

The reviewer required no corrections. Its optional observation about Build Arena's `pyright_errors` axis was investigated against the local scorer source. That inspection proved the scorer requires Pyright JSON even though the goal had invoked mypy text output, so the goal, dependency set, CI gate, and documentation were aligned to Pyright while retaining strict mypy.

A sealed focused Opus review of that semantic delta completed with actual model `claude-opus-4-8`, no required corrections, and verdict `ACCEPT`. The final optional wording cleanup removes a non-load-bearing Ruff file-count detail while preserving the verified PASS result.
