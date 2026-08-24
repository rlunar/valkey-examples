# Example Pull Request

## Approved proposal

Link the approved proposal issue.

## Learning outcome

Describe the Valkey behavior and expected observable result.

## Verification

- [ ] `example.yaml` validates against the repository schema.
- [ ] `make setup`, `make start`, `make verify`, `make reset`, and `make stop` pass.
- [ ] The journey uses real Valkey and released public dependencies.
- [ ] Runtime and direct dependencies are pinned and application lockfiles are committed.
- [ ] Expected output and relevant Valkey state are asserted.
- [ ] Required architecture and behavior diagrams are embedded and match the implementation.
- [ ] Cleanup succeeds after both a complete and a partial run.
- [ ] Security and production limitations are documented.
- [ ] Primary and backup owners and reviewers are present.
- [ ] An uninvolved reviewer reproduced the journey from a clean clone.

## Security

Describe exposed ports, authentication and TLS choices, credentials, data
sensitivity, dependency changes, and any time-limited exception.
