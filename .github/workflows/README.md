# Workflow plan

`validate.yml` provides bootstrap structural, Markdown, and link validation.

Before the first runnable capsule is admitted, maintainers must add blocking
workflows for:

- changed-capsule runtime and journey validation;
- the weekly full Valkey and client compatibility matrix;
- secret, dependency, container-image, workflow, and license scanning; and
- generated catalog publication.

The runtime matrix must come from validated manifests. A missing implementation
must fail rather than silently skip its declared checks.
