# Decision: Represent deployment uncertainty explicitly

Date: 2026-07-30
Status: accepted

## Context

The deployment endpoint can return HTTP 403 for restricted FMC accounts. Returning an empty device list converted that permission denial into “all devices are in sync.” Filtering an unknown device name produced the same false-success shape.

## Decision

Return explicit status values:

- `ok` for confirmed deployment data;
- `unavailable` with `permission_denied` for HTTP 403;
- `not_found` when a requested device is absent from the managed-device inventory.

Synchronization booleans are `null` whenever state is unknown. A named device is reported synchronized only after it is found in inventory and absent from the deployable list.

## Rationale

Unknown is not success. The MCP response must preserve the FMC evidence boundary so an operator or model cannot act on fabricated certainty.

## Alternatives considered

- Raise every 403 as an unstructured tool error — rejected because callers benefit from a stable machine-readable unavailable state.
- Keep returning an empty list — rejected because it lies about synchronization.
- Treat every unmatched name as synchronized — rejected because it conflates unknown devices with known clean devices.

## Consequences

- Existing callers receive a new `status` field and must handle unknown states.
- Restricted accounts remain usable for other read-only resources.
- A filtered status check performs a device-inventory read to distinguish not-found from synchronized.

## Evidence

- `tests/test_resources.py`
- `src/fmc_mcp/client.py`
- `src/fmc_mcp/resources.py`
- `src/fmc_mcp/tools.py`

## Supersession

- Supersedes: none
- Superseded by: none
