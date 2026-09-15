# Catalog tooling

Catalog tooling will convert validated `example.yaml` manifests and compatibility
results into human-readable and machine-readable indexes.

It must be deterministic and must never infer maintained status from directory
names. Generated indexes must expose `level` as an exact L100–L500 filter and
use the labels defined in `docs/authoring.md`.
