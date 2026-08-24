# Agent Instructions

These instructions apply to the entire repository. A deeper `AGENTS.md`
provides additional instructions for its subtree.

## Before changing files

1. Inspect `git status` and preserve unrelated work.
2. Read `README.md`, `CONTRIBUTING.md`, and the relevant design proposal.
3. Resolve the exact target path before creating or moving files.
4. State the resolved capability and path in your working notes.

The target path is resolved in this order:

1. an exact path supplied by the user;
2. the proposal front matter's `proposed_path`;
3. an existing capsule path; then
4. the repository taxonomy when no path has been decided.

Once resolved, use the path exactly. Do not substitute a similar capability,
rename the slug, reorder its terms, or move it to a category that seems more
technically descriptive.

## Taxonomy contract

Example capsules use:

```text
examples/<capability>/<implementation-slug>/
```

The current convention for a single-language implementation slug is:

```text
<use-case>-<language>[-<framework>]
```

Directory names are not parsed to derive metadata. `example.yaml` is
authoritative for kind, capability, languages, owners, compatibility, and
lifecycle.

A capability is valid only when it appears in all three locations:

1. `schemas/example.schema.json`;
2. `examples/README.md`; and
3. `examples/<capability>/README.md`.

When the user approves a new capability, update all three locations in the same
change. Choose the capability from the user's primary learning goal. Describe
the Valkey commands, data structures, clients, and frameworks as implementation
mechanisms rather than replacing the requested capability with one of them.

## Proposal gate

For work under `docs/proposals/`, read
[`docs/proposals/AGENTS.md`](docs/proposals/AGENTS.md).

A proposal with `status: Draft` authorizes documentation work only. Create
runtime code only after the user explicitly requests implementation.

The proposal's `proposed_path` is the single source of truth for the future
capsule path. Search for stale paths after changing it.

## Capsule gate

For work under `examples/`, read
[`examples/AGENTS.md`](examples/AGENTS.md).

Create a capsule only at the proposal's exact `proposed_path`. If no proposal
exists or its path is ambiguous, resolve the proposal before creating code.

## Repository invariants

- Keep every capsule independently runnable, copyable, and removable.
- Keep runtime dependencies and lockfiles inside the capsule.
- Share schemas, catalog tooling, CI orchestration, and documentation only.
- Use the capsule interface: `make setup`, `make start`, `make verify`,
  `make reset`, and `make stop`.
- Follow the applicable guide under `docs/languages/`.
- Add directories only when they contain required files.
- Pin direct dependencies, runtime versions, and container images.
- Bind local services to loopback and document non-production security choices.
- Use real Valkey in integration and journey tests.
- Apply the diagram contract in `docs/authoring.md` to every proposal and
  capsule; prefer Mermaid embedded beside its explanatory prose.

## Completion criteria

Before reporting completion:

1. confirm every changed proposal path is identical across front matter,
   narrative, indexes, and the planned tree;
2. confirm every capability is synchronized across the schema and category
   documentation;
3. run `bash tools/ci/check-structure.sh`;
4. run Markdown lint for documentation changes;
5. validate changed JSON and YAML files;
6. confirm required diagrams match the documented architecture and behavior;
7. run `git diff --check`; and
8. report which checks actually ran.
