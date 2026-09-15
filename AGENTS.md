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
authoritative for kind, capability, level, languages, owners, compatibility,
and lifecycle.

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

- Keep every application capsule runnable and removable through its own
  `Makefile`; copy the shared `infra/` capsule with it when moving it outside
  this repository.
- Keep runtime dependencies and lockfiles inside the capsule.
- Share schemas, catalog tooling, CI orchestration, and documentation templates
  through repository-root modules. Share local database orchestration through
  the root `infra/` capsule only.
- Require every `example.yaml` to declare `infrastructure.capsule:
  ../../../infra` and the exact profiles it uses.
- Require every `example.yaml` to declare one L100–L500 learning level using
  the definitions in `docs/authoring.md`.
- Keep application runtime code local. Shared infrastructure may provide
  Compose services, Make includes, readiness helpers, and lifecycle shell
  functions, but no Valkey application behavior.
- Use the capsule interface: `make setup`, `make start`, `make verify`,
  `make reset`, and `make stop`.
- Follow the applicable guide under `docs/languages/`.
- Add directories only when they contain required files.
- Pin direct dependencies, runtime versions, and container images.
- Bind local services to loopback and document non-production security choices.
- Use real Valkey in integration and journey tests.
- Apply the diagram contract in `docs/authoring.md` to every proposal and
  capsule; prefer Mermaid embedded beside its explanatory prose.
- Keep `docs/SCRIPT_REEL.md` at 60 seconds or less and make
  `docs/SCRIPT_VIDEO.md` reach its primary runnable build by `05:00`.

## Completion criteria

Before reporting completion:

1. confirm every changed proposal path is identical across front matter,
   narrative, indexes, and the planned tree;
2. confirm every proposal, manifest, and capsule README uses the same level;
3. confirm every capability is synchronized across the schema and category
   documentation;
4. run `bash tools/ci/check-structure.sh`;
5. run Markdown lint for documentation changes;
6. validate changed JSON and YAML files;
7. confirm required diagrams match the documented architecture and behavior;
8. run `git diff --check`; and
9. report which checks actually ran.
