# Security Policy

## Supported versions

Security fixes target the current `main` branch and the latest published package version. Older commits are not maintained as separate release lines.

## Reporting a vulnerability

Do not include credentials, FMC addresses, configuration exports, or exploit details in a public issue.

Use GitHub's private vulnerability-reporting or draft security-advisory flow for this repository. If that channel is unavailable, contact the repository owner through the GitHub profile and request a private channel before sending details.

Include:

- affected version or commit;
- a minimal reproduction with secrets removed;
- impact and required preconditions;
- whether the issue affects FMC confidentiality, integrity, availability, authentication, or transport security;
- any proposed mitigation.

## Operational security

- Use a dedicated read-only FMC account.
- Set `FMC_VERIFY_SSL=true` outside isolated labs and use a trusted certificate.
- Keep `.env` out of version control.
- Keep HTTP transport on loopback unless an external access-control layer is in place.
- Rotate credentials immediately if they are exposed in logs, issues, or chat.
