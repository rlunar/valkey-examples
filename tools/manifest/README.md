# Manifest tooling

Manifest tooling will validate:

- `example.yaml` against `schemas/example.schema.json`;
- the required L100–L500 learning level;
- owner presence and repository review coverage;
- compatibility declarations;
- immutable image references;
- capsule interface commands; and
- catalog and runtime-matrix inclusion.

It must fail closed when a maintained capsule cannot be validated.
