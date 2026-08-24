# Contributing

Valkey Examples uses proposal-first admission. The repository is a maintained
educational catalog, not a general-purpose project incubator.

## Placement test

A contribution belongs here only when every answer is yes:

1. Is teaching observable Valkey behavior its primary purpose?
2. Is it a cookbook, focused demo, or sample application?
3. Can the default journey run from a clean clone with released public
   dependencies?
4. Is the default journey credential-free and vendor-neutral?
5. Can CI execute and assert the journey against real Valkey?
6. Are primary and backup owners and qualified reviewers available?
7. Can the example share this repository's lifecycle without independent
   releases or security advisories?

A no to questions 1–5 means reject or redirect. A no to question 6 means defer.
A no to question 7 means propose a purpose-built repository.

## Proposal process

1. Open an example proposal using the repository issue form.
2. Obtain scope approval from a repository maintainer and a qualified
   language or domain reviewer.
3. Implement one independently runnable capsule.
4. Run the capsule's full documented journey from a clean clone.
5. Open a pull request using the repository template.
6. Obtain a second clean-clone reproduction from a reviewer who did not author
   the capsule.

Proposal approval reserves scope. It does not guarantee that an implementation
will be merged.

## Directory naming

Use:

```text
examples/<capability>/<use-case>-<language>/
```

Use lower-case kebab-case. Name the directory for the Valkey learning goal, not
for a vendor, cloud, model provider, or framework.

Multi-language sample applications may omit the language suffix and place
capability-named implementations beneath `services/`.

## Capsule interface

Every capsule must contain:

- `example.yaml`, validated by `schemas/example.schema.json`;
- a `README.md` describing audience, prerequisites, learning objective,
  expected output, security limitations, and cleanup;
- a capsule-owned `Makefile`;
- language-native version declarations, manifests, and lockfiles;
- automated behavioral assertions against real Valkey; and
- deterministic fixtures when data is required.

Every capsule must implement:

```shell
make setup
make start
make verify
make reset
make stop
```

The commands must be idempotent where practical. `make stop` must be safe after
a partial startup failure. CI must not silently skip a command or replace real
Valkey behavior with mocks.

## Reproducibility

Capsules must:

- pin direct dependencies and commit application lockfiles;
- pin container images by immutable version and digest;
- use released, publicly retrievable dependencies;
- declare Valkey, client, runtime, framework, data, and model versions;
- use health checks instead of fixed startup sleeps;
- state CPU, memory, disk, download, and timeout budgets;
- avoid network access after the documented setup phase when practical; and
- remove containers, volumes, temporary credentials, and generated data.

## Security

Local convenience must have an explicit limit. Capsules must:

- bind published ports to loopback by default;
- commit no credentials, tokens, private keys, or realistic reusable passwords;
- explain when local no-auth or no-TLS settings are unsafe outside development;
- avoid unbounded keyspace operations and unsafe interpolation;
- use non-root containers where supported;
- document data sensitivity and deletion behavior; and
- pass the repository's blocking security, dependency, image, secret, and
  license checks before promotion.

## Review

An example cannot enter `maintained` status until:

- its manifest and ownership are valid;
- native formatting, linting, type checking, compilation, and tests pass;
- the documented primary journey runs against real Valkey;
- expected output and relevant Valkey state are asserted;
- cleanup succeeds;
- the supported compatibility matrix passes; and
- an uninvolved reviewer completes the journey from a clean clone.

Framework coverage by itself is not an admission reason. A proposal must teach
distinct Valkey behavior, serve an unmet audience, or add a materially useful
language path.
