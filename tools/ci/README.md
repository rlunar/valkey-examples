# CI tooling

This directory contains repository validation only. Shared local runtime
orchestration belongs in `infra/`; application runtime behavior must remain in
the example capsules.

`check-structure.sh` performs bootstrap checks that require no third-party
dependencies, including schema-version, infrastructure-capsule, and
proposal/manifest/README level alignment.
