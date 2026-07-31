# Current repository status

Last updated: 2026-07-30

## Deterministic readiness

The maintained baseline requires:

- Python 3.10–3.13 test coverage;
- at least 80% branch coverage;
- Ruff lint and format checks;
- strict mypy over source and tests;
- Pyright with machine-readable output for Build Arena scoring;
- pre-commit hooks;
- reproducible `uv.lock` synchronization;
- wheel and source-distribution build;
- clean wheel installation and package import;
- runtime dependency audit with no known vulnerabilities;
- MCP tool/resource registry smoke;
- CodeQL analysis;
- a passing aggregate `CI gate` before merge.

`main` is governed through GitHub pull requests and the protected-path rules in `docs/method/PROJECT.md`.

## Correctness baseline

- Every FMC HTTP attempt is rate- and connection-limited.
- Concurrent stale-token refreshes are coalesced.
- Missing token headers fail authentication clearly.
- Pagination does not rely solely on `paging.count`.
- Deployment permission denial and unknown device names produce explicit unknown states.
- Invalid operational configuration fails before server startup.

## External boundary

Ordinary CI does not certify a real FMC appliance. Before a release or production rollout, run the opt-in read-only live gate against an authorized sandbox:

```bash
FMC_LIVE_TEST=1 uv run --extra dev python -m pytest -q -m live
```

No production or appliance-readiness claim is valid unless that gate has passed for the target FMC version and credential role.
