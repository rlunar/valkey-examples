# {{CAPSULE_TITLE}} Video Plan

## Production brief

- Working title: <!-- TODO -->
- Audience: <!-- TODO -->
- Format: terminal capture / narrated walkthrough / edited explainer
- Target duration: <!-- TODO -->
- Aspect ratio and resolution: <!-- TODO -->
- Demo source: `make demo`
- Runbook source: [`DEMO.md`](DEMO.md)
- Tutorial source: [`TUTORIAL.md`](TUTORIAL.md)
- Reel-script source: [`SCRIPT_REEL.md`](SCRIPT_REEL.md)
- Tutorial-script source: [`SCRIPT_VIDEO.md`](SCRIPT_VIDEO.md)
- Output path: `.artifacts/<!-- TODO -->.mp4`

## Story promise

<!-- TODO: Start with "You will" and describe what your viewer will understand or prove. -->

## Beat sheet

| Time | Visual | Narration | Evidence |
| --- | --- | --- | --- |
| 00:00 | TODO | TODO | TODO |
| 00:10 | TODO | TODO | TODO |
| 00:30 | TODO | TODO | TODO |
| 00:50 | TODO | TODO | TODO |

Every beat must use verified source, commands, diagrams, or output from the
capsule. Avoid decorative terminal activity that does not advance the learning
objective.

## Capture plan

### Terminal-only adapter

The tape or capture command should invoke `make demo` rather than reproduce its
HTTP requests, sleeps, or cleanup logic.

```text
TODO: tape path and render command
```

### Edited or narrated adapter

List the source excerpts, diagrams, screenshots, captions, and rendered assets
needed by the editor. Keep editable diagram source beside the documentation it
explains.

## Narration and captions

- Address your viewer as "you."
- Use active voice and name the component that performs each action.
- Write for speech rather than reading code verbatim.
- Explain the Valkey behavior before framework mechanics.
- Caption every spoken line and important terminal outcome.
- Do not rely on color alone to distinguish success, failure, or topology.
- Spell out uncommon acronyms on first use.
- Use a short pop culture reference only when it makes a difficult idea easier
  to remember.

## Verification take

Before final capture:

```shell
make verify
make demo
make stop
```

Record the exact versions, selected topology, expected output, and capture
toolchain used for the published take.

## Publication checklist

- [ ] The video follows `DEMO.md` and does not fork the journey.
- [ ] The tutorial and video use current commands and output.
- [ ] No secrets, personal data, unrelated windows, or unstable identifiers appear.
- [ ] Captions, code, diagrams, and terminal text are legible.
- [ ] Rendered media stays in `.artifacts/` unless explicitly admitted.
- [ ] The final frame states the learning takeaway and cleanup status.
- [ ] The script uses active voice and addresses the viewer as "you."
