# Schemas

- `example.schema.json` defines the machine-readable capsule contract,
  including the required L100–L500 learning level.
- `compatibility.schema.json` defines the repository compatibility matrix.
- `example.template.yaml` is the starting point for a new capsule manifest.

The current example manifest version is `2`; it requires one `level` value
from `L100`, `L200`, `L300`, `L400`, or `L500`.

Catalog and CI discovery must use validated manifests rather than directory
heuristics.
