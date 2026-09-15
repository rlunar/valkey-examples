# Build {{CAPSULE_TITLE}}

## Read this first

<!--
TODO:
- Tell your reader what they should know in plain language.
- Summarize the complete program in three to five steps.
- Tell your reader which sections form the shortest learning path.
- Use active voice and address your reader as "you."
- Add one useful memory hook when a pop culture reference clarifies a hard
  idea.
-->

## Key words

<!-- TODO: Define each required technical term in one short sentence. -->

## Learning outcome

<!-- TODO: Start with "You will" and state what your reader builds, observes, and understands. -->

## Audience and prerequisites

- Audience: <!-- TODO -->
- Prior knowledge: <!-- TODO -->
- Required tools: <!-- TODO -->
- Expected completion time: <!-- TODO -->

## Tutorial contract

Build toward the same behavior exposed by:

```shell
make demo
```

In each stage, you should include:

1. one conceptual change;
2. the exact files or commands involved;
3. a small executable checkpoint;
4. the expected output; and
5. a short explanation of why the result matters.

## Suggested chapter sequence

1. Initialize the language-native project and lock dependencies.
2. Define the smallest Valkey connection or data model.
3. Implement the primary Valkey commands.
4. Add the application adapter, when one exists.
5. Connect the capsule to its declared shared infrastructure profiles.
6. Add unit, real-Valkey integration, and journey tests.
7. Add `make demo`, bounded reset, and safe cleanup.
8. Run the finished journey and explain the stored state.

## Checkpoint template

Repeat this shape for each implementation stage:

### TODO: Stage title

Change:

```text
TODO
```

Run:

```shell
TODO
```

Expected result:

```text
TODO
```

Explain:

> TODO

## Shared infrastructure

Reference the capsule's `example.yaml`, its application-only Compose fragment,
and the root `infra/` profiles. Do not copy shared Valkey, PostgreSQL, TLS,
readiness, or cleanup implementation into the tutorial as local files.

## Final verification

```shell
make setup
make verify
make demo
make reset
make stop
```

## Final takeaway

<!-- TODO: Start with "You can now" and summarize the Valkey behavior in one sentence. -->
