# Security Policy

## Reporting a vulnerability

Do not report a suspected vulnerability in a public issue.

Use the repository's private vulnerability-reporting form under the GitHub
Security tab. If private reporting is not enabled, contact a Valkey project
maintainer through the private channel listed by the Valkey project before
sharing exploit details.

Include:

- the affected capsule and version or commit;
- reproduction steps;
- expected and observed impact;
- whether credentials or network access are required; and
- any suggested mitigation.

## Catalog response

A known critical vulnerability removes the affected capsule from the
maintained catalog until remediation is verified.

Security-critical and secret-scanning gates cannot be waived for catalog
promotion. Other temporary exceptions must name an approver, owner, reason,
compensating control, and expiry date in the capsule manifest.

## Educational-code warning

Examples are not production certification. Each capsule must explain simplified
security and operational choices, particularly local no-auth, no-TLS, published
ports, test credentials, and reduced resource limits.
