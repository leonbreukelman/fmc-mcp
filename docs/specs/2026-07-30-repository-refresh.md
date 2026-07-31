# Repository refresh and readiness specification

Status: accepted for implementation
Date: 2026-07-30

## Owner outcome

Land one reviewed maintenance PR that leaves `main` synchronized, deterministic, secure against known dependency advisories, and ready for new feature work. Preserve recoverable backups before removing stale local or remote work.

## In scope

- Preserve the unpublished local commit and all non-ignored untracked work before cleanup.
- Publish the valid project-method scaffold after removing host-specific paths.
- Keep the runtime on the compatible MCP 1.x line; treat MCP 2.x as a separate migration.
- Replace ambiguous deployment-status success with explicit unavailable and not-found results.
- Reject invalid FMC and MCP configuration at startup.
- Apply rate and concurrency limits to authentication, retries, and normal API requests.
- Serialize token refresh so concurrent 401 responses do not create a refresh storm.
- Validate auth response headers and support both forms of `Retry-After`.
- Make pagination robust when FMC omits or misreports `paging.count`.
- Raise coverage to the project floor and add clean-wheel and runtime dependency-audit gates.
- Test supported Python versions in CI, refresh action versions, add dependency and code-scanning automation, and protect `main` after merge.
- Align README, specification, security, lifecycle, decision, status, and verification documentation.
- Merge through a GitHub PR, verify the landed commit, and remove archived stale worktrees and branches.

## Out of scope

- MCP 2.x API migration.
- Writes to FMC configuration or device state.
- Changing the backwards-compatible lab default for TLS verification. Production deployments must explicitly enable verification.
- Claiming live FMC compatibility without an authorized read-only FMC sandbox credential set.

## Compatibility rules

- Public interfaces and registered MCP resources/tools remain available.
- Existing valid environment configurations remain accepted.
- Invalid non-positive limits/timeouts and malformed MCP transport/port values fail clearly rather than degrading at runtime.
- Deployment permission denial and unknown device names never report a successful synchronization state.
- Every actual HTTP attempt consumes rate-limit capacity.

## Acceptance gates

1. `uv lock --check`
2. `uv run --extra dev python -m pytest -q`
3. `uv run --extra dev python -m pytest --cov=src/fmc_mcp --cov-report=term-missing --cov-fail-under=80 -q`
4. `uv run --extra dev ruff check .`
5. `uv run --extra dev ruff format --check .`
6. `uv run --extra dev python -m mypy src tests`
7. `uv run --extra dev pre-commit run --all-files`
8. Build wheel and source distribution.
9. Install the wheel with dependencies in a clean environment and import `fmc_mcp`.
10. Export and audit runtime dependencies with no known vulnerabilities.
11. Parse all staged JSON, scan staged public content for credentials and host-private data, and pass `git diff --cached --check`.
12. Independent Opus implementation review has no blocking findings.
13. GitHub PR checks pass on the exact head commit.
14. The merge commit passes the post-merge local and GitHub gates.
15. Canonical local `main` equals `origin/main`, has an empty `git status --short`, and stale archived refs/worktrees are removed.

## Publication boundary

The GitHub repository is public. The PR may publish source, tests, workflows, dependency metadata, and sanitized project documentation. Raw local audit logs, model wrapper JSON, absolute home/temp paths, credentials, caches, private runtime data, and backup archives remain outside Git history.

## Remaining external certification boundary

Deterministic local/CI readiness does not prove interoperability with a real FMC appliance. A later release gate must run the explicit read-only smoke against an authorized sandbox and fail on required endpoint errors.
