# Documentation Templates

These repository-wide templates scaffold capsule-owned documentation without
coupling authoring guidance to the shared infrastructure implementation.

The templates are:

- [`DEMO.md`](DEMO.md), an executable presenter runbook;
- [`TUTORIAL.md`](TUTORIAL.md), a staged build-from-scratch learning path;
- [`SCRIPT_REEL.md`](SCRIPT_REEL.md), a spoken short-form script capped at 60
  seconds;
- [`SCRIPT_VIDEO.md`](SCRIPT_VIDEO.md), a longer tutorial script whose primary
  build reaches `make demo` by five minutes; and
- [`VIDEO.md`](VIDEO.md), a storyboard, narration, capture, and publication
  plan.

Write every generated document in active voice and address your audience as
"you." You may add a short pop culture reference when it helps your audience
remember a difficult idea, but the technical explanation must stand on its
own.

Create only the missing documents for an example capsule from the repository
root:

```shell
make -C infra docs-init \
  CAPSULE=examples/<capability>/<implementation-slug>
```

The command reads these templates but writes the rendered copies into the
example capsule. Existing capsule documents are never replaced.
