# Cisco FMC read-only MCP server design

Status: implemented baseline
Last updated: 2026-07-30

## Purpose

Expose Cisco Firepower Management Center inventory and deployment context through MCP without changing FMC configuration or device state.

The data plane is read-only. It performs GET requests for version, device, object, and deployment data. Authentication uses FMC's required token-generation and token-refresh POST endpoints; those calls do not mutate firewall configuration.

## Supported runtime

- Python 3.10–3.13
- MCP Python SDK 1.28.1 through the latest compatible 1.x release
- Cisco FMC 7.4.x
- stdio transport by default; HTTP/SSE is opt-in

MCP 2.x is deliberately excluded until a separate API migration is implemented and tested.

## Components

| Component | Responsibility |
| --- | --- |
| `src/fmc_mcp/config.py` | Validate FMC credentials, operational limits, and MCP listener settings. |
| `src/fmc_mcp/client.py` | Authenticate, rate-limit every HTTP attempt, bound concurrency, refresh tokens, parse retries, and paginate. |
| `src/fmc_mcp/resources.py` | Format passive MCP resources. |
| `src/fmc_mcp/tools.py` | Execute read-only IP search and deployment-status queries. |
| `src/fmc_mcp/server.py` | Register MCP resources/tools and manage the FMC client lifecycle. |

## MCP surface

### Resources

| URI | Result |
| --- | --- |
| `fmc://system/info` | FMC server version and platform information. |
| `fmc://devices/list` | Managed firewall device summaries. |
| `fmc://objects/network` | Network object summaries. |
| `fmc://deployment/status` | Pending deployment data or an explicit unavailable state. |

### Tools

| Tool | Result |
| --- | --- |
| `search_object_by_ip` | Network and host objects containing an IPv4 or IPv6 address. |
| `get_deployment_status` | Pending state for all devices or one validated device name. |

## Authentication and retry contract

1. Generate an access and refresh token with FMC Basic Auth.
2. Reject a nominal success response if either required token header is missing.
3. Send the access token on every data request.
4. On 401, serialize refresh under a lock. Concurrent requests that failed with the same stale token share one refresh.
5. After three refreshes, perform a full token generation request.
6. On 429, honor delta-seconds or HTTP-date `Retry-After`; invalid values use 60 seconds and any wait is capped at five minutes.
7. Every authentication, data, and retry attempt consumes one rate-limit token and one connection slot.

## Rate and connection limits

Defaults match the project FMC contract:

- 120 HTTP attempts per minute, implemented as a token bucket with a two-token-per-second refill.
- 10 concurrent HTTP attempts, enforced by both the client connection pool and an asyncio semaphore.
- 60-second request timeout.

Non-positive values fail configuration validation before runtime primitives are constructed.

## Pagination contract

List endpoints request up to 1,000 expanded items at a time. The client continues when the response supplies `paging.next`, when a full page is returned, or when a reported total indicates more items. It stops on an empty page or a short final page. `paging.count` is advisory rather than the sole completion signal.

## Deployment-status semantics

- `status: "ok"`: FMC returned deployment data.
- `status: "unavailable", reason: "permission_denied"`: FMC returned 403. Synchronization fields are unknown, not successful.
- `status: "not_found"`: a requested device name does not exist in the managed-device inventory. Synchronization is unknown.
- A known device absent from the deployable list is reported as synchronized.

## Security boundary

- Credentials are loaded from environment variables or an ignored `.env` file and are never logged.
- Authentication errors log status codes, not response bodies.
- TLS verification remains disabled by default for backwards-compatible lab use. Production deployments must set `FMC_VERIFY_SSL=true` and use a trusted certificate.
- HTTP transport binds to loopback by default. Operators must add their own network access controls before binding more broadly.
- Vulnerability reports follow `SECURITY.md`.

## Verification contract

The deterministic gate covers unit tests, branch coverage of at least 80%, Ruff, strict mypy, Pyright-compatible Build Arena scoring, pre-commit, package build, clean wheel installation/import, runtime dependency audit, MCP registry smoke, Python 3.10–3.13 CI, and CodeQL.

The real-appliance boundary is separate: `FMC_LIVE_TEST=1` enables a read-only smoke that hard-fails required version, device, network, host, resource, and tool paths. It requires an authorized sandbox credential set and is not implied by ordinary CI.