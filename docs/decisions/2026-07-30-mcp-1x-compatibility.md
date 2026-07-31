# Decision: Keep the runtime on supported MCP 1.x

Date: 2026-07-30
Status: accepted

## Context

The unconstrained `mcp>=1.0.0` dependency permits MCP 2.x. A clean installation selected MCP 2.0, where `mcp.server.fastmcp` is absent, and the package failed to import. The existing server is written for the MCP 1.x API.

## Decision

Require `mcp>=1.28.1,<2` and update the lock to the latest compatible 1.x release. Treat MCP 2.x support as a separate migration with its own compatibility tests.

## Rationale

This restores clean-install correctness without mixing a major SDK migration into a maintenance change. The lower bound also removes vulnerable transitive versions found in the previous lock.

## Alternatives considered

- Leave the dependency unconstrained — rejected because clean installation is broken.
- Migrate to MCP 2.x now — rejected because it is a separate API and transport change with a larger regression surface.
- Pin one exact MCP patch — rejected because the compatible 1.x range can receive safe fixes through the lock-update process.

## Consequences

- Fresh installs remain on the API the code currently implements.
- Dependabot can propose compatible 1.x updates.
- MCP 2.x features remain unavailable until an explicit migration lands.

## Evidence

- `docs/specs/2026-07-30-repository-refresh.md`
- CI clean-wheel installation and import gate
- Runtime dependency-audit gate

## Supersession

- Supersedes: none
- Superseded by: none
