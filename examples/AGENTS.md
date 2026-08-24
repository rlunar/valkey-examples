# Example Capsule Instructions

These instructions apply to every example capsule. Follow the root
[`AGENTS.md`](../AGENTS.md) first.

## Admission sequence

1. Locate the approved proposal.
2. Read its `status`, `capability`, and `proposed_path`.
3. Confirm the user authorized implementation.
4. Create the capsule at the exact `proposed_path`.
5. Validate `example.yaml` against `schemas/example.schema.json`.

Stop before creating runtime files when the proposal is missing, remains a
documentation-only draft, or names a different path.

## Capsule contract

The capsule must:

- own its runtime declarations, manifests, lockfiles, source, tests, fixtures,
  container definitions, and cleanup;
- implement `make setup`, `make start`, `make verify`, `make reset`, and
  `make stop`;
- run from a clean clone without paid credentials;
- use real Valkey for integration and journey tests;
- expose the expected behavior and cleanup in its README;
- embed the diagrams required by [`docs/authoring.md`](../docs/authoring.md)
  beside the prose they explain;
- contain no empty directories; and
- import no runtime code from another capsule or repository-level helper.

Follow the language guide referenced by the proposal. If a required language
guide is missing, add or approve that guide before implementation.

## Metadata alignment

The manifest must match the approved proposal:

- `id` matches the capsule identity;
- `capability` matches the proposal and schema enum;
- `languages` describes the implementation, independent of directory parsing;
- image references contain an immutable digest;
- owners are real primary and backup handles; and
- status remains `candidate` until every promotion gate passes.

## Completion criteria

Before reporting implementation complete:

1. execute every capsule `make` target;
2. run native formatting, linting, type checking, and tests;
3. run the real-Valkey integration and documented journey tests;
4. verify cleanup after both complete and partial startup;
5. verify diagrams match the implemented architecture and observed journey;
6. validate the manifest and repository structure;
7. run `git diff --check`; and
8. distinguish checks executed from checks only documented.
