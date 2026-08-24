# Authoring an Example Capsule

## Start with the learning objective

State:

1. what Valkey capability or pattern is being taught;
2. what the user will run;
3. what observable output or state proves the behavior; and
4. why Valkey is material to the result.

Framework or client coverage alone is not a learning objective.

## Choose the content kind

- Use a **cookbook** for a guided sequence with executable steps.
- Use a **demo** for the smallest complete program demonstrating one capability.
- Use a **sample application** for a coherent journey combining multiple
  capabilities.

The kind belongs in `example.yaml`; it does not create another directory layer.

## Keep the capsule independent

A capsule owns its runtime version declarations, project manifests, lockfiles,
fixtures, tests, container definitions, and cleanup.

It may use root schemas and CI orchestration, but it must not import a shared
repository runtime library or another capsule.

## Implement the capsule interface

The `Makefile` is the stable seam used by readers, reviewers, and CI:

```shell
make setup
make start
make verify
make reset
make stop
```

Language-native commands remain visible inside these targets and in the README.
The interface is not permission to replace ecosystem conventions with shell
logic.

## README requirements

Every capsule README must include:

- audience and prerequisites;
- learning objective and expected output;
- a link to the Valkey-specific implementation;
- exact setup, startup, verification, reset, and cleanup commands;
- supported Valkey, client, and runtime versions;
- CPU, memory, disk, download, and time expectations;
- architecture and data flow for sample applications;
- local security choices and production differences;
- data, model, and third-party licenses; and
- ownership, status, and support expectations.

Every primary-path command shown in the README must run in CI.

## Diagram contract

Every example capsule must embed at least one explanatory diagram in its
`README.md` or `DESIGN.md`. Prefer fenced Mermaid diagrams because their source
is reviewable, diffable, and rendered with the surrounding documentation.

Choose diagrams that explain the learning path:

- use an architecture diagram for modules, adapters, processes, and stores;
- use a sequence diagram for time-ordered requests, responses, retries, or
  success and failure branches;
- use a flowchart for decision logic; and
- use a data model or state diagram when stored structure or transitions are
  the learning objective.

A request/response demo with materially different outcomes should include both
an architecture diagram and a sequence diagram covering the primary success
and failure responses.

Place each diagram beside the narrative it explains: introduce the question or
flow, embed the diagram, then explain the important nodes and arrows in prose.
Keep labels, commands, ports, status codes, and implementation names
synchronized with the runnable capsule. Split a dense diagram rather than
shrinking it into an unreadable overview.

When Mermaid cannot express the diagram clearly, commit the editable source
and an accessible rendered asset. Generated media never replaces the editable
source.

## Multi-language sample applications

Keep the journey and contracts stable while implementations vary:

```text
examples/search/semantic-commerce/
├── example.yaml
├── README.md
├── Makefile
├── contracts/
├── journey/
├── frontend/
├── services/
│   ├── search-python/
│   ├── session-go/
│   └── recommendations-java/
├── deploy/
│   ├── compose.yaml
│   └── providers/
└── tests/
    ├── contract/
    └── end-to-end/
```

Provider overlays are optional adapters and cannot replace the credential-free
local journey.
