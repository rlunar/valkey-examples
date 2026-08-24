# Proposal Instructions

These instructions apply to design proposals in this directory. Follow the
root [`AGENTS.md`](../../AGENTS.md) first.

## Authoring sequence

1. Read the user's requested capability and exact path.
2. Check the capability enum in `schemas/example.schema.json`.
3. Check the controlled vocabulary in `examples/README.md`.
4. Record the exact path once in front matter as `proposed_path`.
5. Use that value unchanged in the decision request, planned tree, acceptance
   criteria, and proposal index.
6. Search the repository for superseded capability names and paths.

The proposal is complete only when the front matter, proposal index, schema,
category documentation, and every narrative path agree.

## Capability selection

Choose the capability from the user's primary learning goal.

For example, a rate-limiting demonstration belongs to `rate-limiter` even when
its implementation teaches sorted sets. Record sorted sets, Lua, GLIDE, Flask,
or another mechanism in the architecture and dependency sections.

When the requested capability is new, add it to:

- `schemas/example.schema.json`;
- `examples/README.md`; and
- `examples/<capability>/README.md`.

## Path contract

Treat `proposed_path` as opaque and authoritative. Do not parse the final path
segment to infer or rewrite the language, framework, or use-case ordering.

An exact user-supplied path overrides a previously proposed path. Update all
references in the same change.

## Draft scope

`status: Draft` means documentation only. A draft may describe planned source
files, commands, tests, and runtime behavior, but it must not create the capsule
or application implementation.

## Proposal validation

Before completion:

1. validate front matter as YAML;
2. verify all relative links;
3. run Markdown lint;
4. run `bash tools/ci/check-structure.sh`;
5. run `git diff --check`; and
6. confirm only authorized documentation and taxonomy files changed.
