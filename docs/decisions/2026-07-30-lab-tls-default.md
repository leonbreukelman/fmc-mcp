# Decision: Preserve the lab TLS default with an explicit production requirement

Date: 2026-07-30
Status: accepted

## Context

Many FMC labs use self-signed certificates, and the existing default disables certificate verification. Changing the default in a maintenance refresh would break existing lab configurations. Leaving the risk implicit is unacceptable for production use.

## Decision

Preserve `FMC_VERIFY_SSL=false` for backwards compatibility in this release. Keep the runtime warning, document `FMC_VERIFY_SSL=true` as mandatory outside isolated labs, and treat a secure-default change as a future breaking release decision.

## Rationale

This avoids an unannounced compatibility break while making the production requirement explicit in the README, design, environment example, and security policy.

## Alternatives considered

- Change the default to `true` immediately — rejected for this maintenance release because self-signed lab users would fail on upgrade.
- Keep the default and omit warnings — rejected because it hides a material transport risk.
- Disable TLS verification unconditionally — rejected because production must support verified TLS.

## Consequences

- Existing labs remain functional.
- Production operators must opt in to verification and provide a trusted certificate chain.
- The project still carries a secure-default debt that should be resolved in a breaking release.

## Evidence

- `README.md`
- `.env.example`
- `SECURITY.md`
- `src/fmc_mcp/config.py`

## Supersession

- Supersedes: none
- Superseded by: none
