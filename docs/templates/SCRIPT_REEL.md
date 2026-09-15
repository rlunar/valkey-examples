# {{CAPSULE_TITLE}} Reel Script

## Production contract

- Format: vertical short-form video
- Target duration: 60 seconds maximum
- Timed scope: architecture, cached deployment, observable proof, and takeaway
- Behavioral source: `make demo`
- Runbook source: [`DEMO.md`](DEMO.md)

Run dependency installation, image pulls, full verification, and recovery checks
before recording. The timed take must still show the deployment becoming ready,
unless `make demo` owns startup and cleanup itself.

## Prepare off camera

```shell
make setup
make verify
make stop
```

Confirm that the exact commands and expected output below still match the
capsule.

## 60-second script

| Time | Screen and action | Spoken narration | Evidence |
| --- | --- | --- | --- |
| 00:00–00:05 | <!-- TODO: show the result or problem --> | <!-- TODO: one-sentence hook --> | Learning goal |
| 00:05–00:15 | <!-- TODO: show a focused architecture view --> | <!-- TODO: explain the components and Valkey's role --> | Architecture |
| 00:15–00:30 | <!-- TODO: run the cached startup command --> | <!-- TODO: explain what is being deployed --> | Readiness |
| 00:30–00:50 | <!-- TODO: run `make demo` --> | <!-- TODO: narrate the observable behavior --> | Real Valkey output |
| 00:50–01:00 | <!-- TODO: hold the proof and close --> | <!-- TODO: one-sentence takeaway --> | Final result |

## Exact recording commands

```shell
# TODO: Add the smallest architecture display command.
# TODO: Add the cached deployment command.
make demo
```

## Capture notes

- Record one capability and one primary topology per take.
- Keep terminal text legible in a vertical crop.
- Cut waiting time; do not cut or fabricate command results.
- Caption every spoken line and important result.
- Keep setup, full verification, recovery, and cleanup outside the timed take
  unless they are part of the learning outcome.

## Verification

- [ ] The final edit is no longer than 60 seconds.
- [ ] The architecture explanation names Valkey's role.
- [ ] The recording shows real readiness and behavioral output.
- [ ] The commands match `DEMO.md` and `make demo`.
- [ ] Cleanup succeeds after the take.
