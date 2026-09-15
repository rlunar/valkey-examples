# {{CAPSULE_TITLE}} Tutorial Video Script

## Production contract

- Format: narrated tutorial video
- Target duration: <!-- TODO: usually 4–8 minutes -->
- Primary build complete by: 05:00
- Behavioral source: `make demo`
- Tutorial source: [`TUTORIAL.md`](TUTORIAL.md)
- Production-plan source: [`VIDEO.md`](VIDEO.md)

The five-minute checkpoint covers the canonical build from prepared,
cached dependencies to a runnable capsule and its first successful
`make demo`. Deeper explanation and optional variations may follow.

## Prepare off camera

```shell
make setup
make verify
make stop
```

State any generated starter files, cached images, or prepared checkpoints used
to keep the recorded build deterministic.

## Tutorial script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:20 | <!-- TODO: show the finished behavior --> | <!-- TODO: promise the outcome --> | Finished result |
| 00:20–01:00 | <!-- TODO: show architecture --> | <!-- TODO: explain Valkey's role and data flow --> | Diagram |
| 01:00–02:30 | <!-- TODO: build the core implementation --> | <!-- TODO: explain the essential code --> | Source |
| 02:30–03:30 | <!-- TODO: connect configuration and infrastructure --> | <!-- TODO: explain runtime choices --> | Configuration |
| 03:30–04:20 | <!-- TODO: deploy the cached build --> | <!-- TODO: explain readiness --> | `make start` |
| 04:20–05:00 | <!-- TODO: run the primary journey --> | <!-- TODO: explain the proof --> | `make demo` |
| 05:00+ | <!-- TODO: optional variation, failure, or tradeoff --> | <!-- TODO: deeper explanation --> | Optional evidence |

## Exact recording commands

```shell
# TODO: Add focused display/build commands from TUTORIAL.md.
make start
make demo
make stop
```

## Editing and teaching notes

- Show the shortest complete build before optional files or variations.
- Use prepared checkpoints instead of filming repetitive typing.
- Keep exact commands, source excerpts, and expected results synchronized with
  `TUTORIAL.md`.
- Mark the moment the primary build succeeds before 05:00.
- Caption every spoken line and important terminal result.

## Verification

- [ ] The primary build reaches a successful `make demo` by 05:00.
- [ ] Optional material begins only after the primary checkpoint.
- [ ] The architecture and source excerpts match the current capsule.
- [ ] The video does not implement a journey separate from `make demo`.
- [ ] Cleanup succeeds after the recording.
