# Security policy

## Supported versions

Only the current main branch is supported during the pre-1.0 phase.

## Reporting a vulnerability

Do not open a public issue for vulnerabilities involving credentials, command
execution, permission boundaries, private project memory, or provider access.
Contact the repository owner privately through the hosting platform and include:

- A concise description and impact.
- Reproduction steps.
- Affected files and versions.
- Any known mitigation.

Do not include real secrets or private user data in the report.

## Security boundaries

Brichan must not broaden permissions, access secrets, contact external parties,
deploy, publish, or perform destructive actions without explicit user
authorization. Project memory must not contain credentials or raw private data.
