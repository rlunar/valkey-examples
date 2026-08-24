# Compatibility Policy

## Bootstrap status

The initial supported Valkey, client, and language-runtime matrix has not yet
been approved. `compatibility.yaml` therefore remains in `bootstrap` status and
contains no supported versions.

No capsule may enter `maintained` status until the matrix is active.

## Policy

Every maintained capsule must declare:

- every supported Valkey version;
- the client package and exact tested version;
- language runtime and package-manager versions;
- container images pinned by version and digest; and
- any operating-system or architecture limitations.

Pull requests may test one representative supported Valkey version for speed.
Scheduled and catalog-release workflows must test every version declared by the
capsule.

Versions are removed only through an announced compatibility change. A capsule
tied exclusively to an unsupported Valkey, client, or runtime version must be
updated, deprecated, or archived.
