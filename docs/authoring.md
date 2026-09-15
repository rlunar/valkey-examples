# Authoring an Example Capsule

## Start with the learning objective

State:

1. what Valkey capability or pattern is being taught;
2. what your reader will run;
3. what observable output or state proves the behavior; and
4. why Valkey is material to the result.

Framework or client coverage alone is not a learning objective.

## Choose the content kind

- Use a **cookbook** for a guided sequence with executable steps.
- Use a **demo** for the smallest complete program demonstrating one capability.
- Use a **sample application** for a coherent journey combining multiple
  capabilities.

The kind belongs in `example.yaml`; it does not create another directory layer.

## Choose the level

Assign the level from the knowledge and reasoning needed to complete and
explain the primary learning path:

| Level | Label | Use when the capsule |
| --- | --- | --- |
| `L100` | Beginner | Introduces one core Valkey concept with guided commands and no required Valkey experience |
| `L200` | Intermediate | Combines several concepts in a small application and assumes basic command and client familiarity |
| `L300` | Advanced | Teaches concurrency, transactions, distributed topology, failure behavior, or material operational tradeoffs |
| `L400` | Expert | Requires deep distributed-systems, performance, or security expertise across multiple capabilities |
| `L500` | Maintainer | Teaches internals, extension, compatibility, governance, or ongoing ecosystem and repository maintenance |

Record only the code, such as `level: L200`, in `example.yaml`. Do not increase
the level because the capsule downloads more images, uses more containers, or
contains more lines of code. Reclassify it when the primary learning outcome
or prerequisite knowledge changes materially.

## Write for a high school reader

The learning level describes the technical topic, not the age or reading
level. An L300 capsule may teach transactions or failover, but its first
explanation must still use plain language.

Use these rules:

- define a technical term the first time it appears;
- use one idea per paragraph and one action per numbered step;
- show the shortest working path before build, test, and deployment details;
- explain acronyms such as TLS, TTL, OTLP, and WSGI;
- use concrete names such as "the primary node" instead of abstract phrases
  such as "the selected topology";
- add comments where code must perform a non-obvious safety or concurrency
  step; and
- keep complete reference files after the guided path, not before it.

Every capsule README should tell a new reader:

1. what they need to know before starting;
2. what the program does in three to five plain steps;
3. what the main technical words mean; and
4. which files to read first.

## Use active voice and second person

Address your reader as **you**. Use second person in learning outcomes,
instructions, explanations, and expected results. Do not call people "the
user," "the learner," "the reader," or "one."

Write:

> You run `make demo`, and the application stores one key in Valkey.

Do not write:

> A key is stored in Valkey when the demo is run by the user.

Name the actor before the action. Write "Valkey returns the value" instead of
"the value is returned." Write "the script starts three nodes" instead of
"three nodes are started."

Keep technical components as the subject when they perform the action. For
example, "Sentinel promotes the replica" is clearer than forcing the sentence
to start with "you." Second person should guide the learning journey, not
distort how the system works.

Avoid "we" and "let's." Tell your reader what to do, what they will see, and
why the result matters.

## Use pop culture as a memory hook

You may use a familiar film, television, music, sports, or game reference when
it makes a technical idea easier to remember. State the real behavior first or
immediately after the comparison.

Write:

> A cluster slot works like the Hogwarts Sorting Hat: it assigns each key to
> one shard. Unlike the Sorting Hat, Valkey uses a repeatable calculation, so
> the same key receives the same slot.

Keep references pragmatic:

- use one short reference for a difficult idea, not a running comedy routine;
- make the explanation understandable when someone misses the reference;
- prefer references that many age groups recognize;
- avoid spoilers, stereotypes, politics, and references that may age quickly;
- never place a joke inside a command, error message, or expected output; and
- remove the reference if it takes longer to explain than the technical idea.

## Keep application behavior independent

A capsule owns its runtime version declarations, project manifests, lockfiles,
fixtures, tests, application container definitions, and application cleanup.

It may use root schemas, CI orchestration, and the root `infra/` capsule. It
must not import a shared application runtime library or another example
capsule. `example.yaml` declares the exact shared infrastructure profiles so
the dependency is visible to readers and tooling.

## Implement the capsule interface

The `Makefile` is the stable seam used by readers, reviewers, and CI:

```shell
make setup
make start
make verify
make reset
make stop
```

Language-native commands remain visible inside these targets and in the README.
Repeated database topology, Compose project isolation, readiness, and cleanup
belong behind the `infra/` interface. The interface is not permission to
replace ecosystem conventions or application behavior with shell logic.

## Create runbooks, scripts, tutorials, and video plans

Use the repository-wide templates under
[`docs/templates/`](templates/README.md) to create missing documentation
files. The infrastructure Make target is the scaffolding interface:

```shell
make -C infra docs-init \
  CAPSULE=examples/<capability>/<implementation-slug>
```

The command preserves existing files and scaffolds:

- `docs/DEMO.md` for the executable presenter journey;
- `docs/TUTORIAL.md` for the staged build narrative;
- `docs/SCRIPT_REEL.md` for the spoken short-form recording;
- `docs/SCRIPT_VIDEO.md` for the spoken longer tutorial; and
- `docs/VIDEO.md` for timing, visuals, narration, captions, and publication.

The capsule owns the generated copies. Keep `make demo` as the behavioral
source of truth: runbooks, tutorials, terminal tapes, and edited videos may
present that journey but must not implement a parallel version of it.

The infrastructure capsule's own `infra/docs/` directory is not a template
source. It contains the concrete standalone, Sentinel, and cluster deployment
demos and tutorials that explain the shared infrastructure itself.

## Write scripts for reels and tutorial videos

Keep production scripts separate from executable runbooks:

- `SCRIPT_REEL.md` is the exact spoken and visual script for one vertical reel.
  Its final edit must be no longer than 60 seconds. Run dependency installation,
  image pulls, full verification, and recovery checks off camera. The timed take
  shows a focused architecture view, cached deployment readiness, real Valkey
  behavior, and one takeaway.
- `SCRIPT_VIDEO.md` is the spoken script for a longer tutorial video. The
  canonical build must reach a successful `make demo` checkpoint by `05:00`.
  Optional topologies, failure drills, implementation alternatives, and deeper
  tradeoffs follow that checkpoint.
- `VIDEO.md` remains the production plan for capture, editing, captions,
  assets, output paths, and publication.

State the timing assumptions in each script. Use cached released dependencies
for recording, but never replace real command output with staged text. Keep
`make demo` as the behavioral source of truth for both formats.

Record only one primary topology or implementation in a reel. A tutorial video
may compare variations after the five-minute build checkpoint.

## Make every presentation step executable

Assume presenters have Homebrew, HTTPie, bat, Gum, Glow, jq, and yq. Use those
tools directly in demo runbooks:

- use `glow` to render Markdown context;
- use `bat` to display source code and text configuration with line numbers;
- use `yq -C` to select the relevant part of a YAML file;
- use `jq -C` to select or format JSON;
- use `http` for HTTP requests; and
- use `gum style` for short visual labels when they help the audience follow
  a live presentation.

Never write only "show `compose.yaml`" or "look at `app.py`." Include the exact
copy-pasteable command that displays the relevant content. Select the smallest
section that gives enough context, and then state what your audience should
notice.

Write:

```shell
gum style --bold "Standalone service"
docker compose --profile valkey-standalone config |
  yq -C '.services.standalone'
```

Do not make your audience search a large file while you speak. If you mention
a second file, add a second display command. Keep every command relative to the
directory named at the start of the runbook.

## README requirements

Every capsule README must include:

- audience, declared learning level, and prerequisites;
- learning objective and expected output;
- a link to the Valkey-specific implementation;
- exact setup, startup, verification, reset, and cleanup commands;
- supported Valkey, client, and runtime versions;
- CPU, memory, disk, download, and time expectations;
- architecture and data flow for sample applications;
- local security choices and production differences;
- data, model, and third-party licenses; and
- ownership, status, and support expectations.

Every primary-path command shown in the README must run in CI.

## Diagram contract

Every example capsule must embed at least one explanatory diagram in its
`README.md` or `DESIGN.md`. Prefer fenced Mermaid diagrams because their source
is reviewable, diffable, and rendered with the surrounding documentation.

Choose diagrams that explain the learning path:

- use an architecture diagram for modules, adapters, processes, and stores;
- use a sequence diagram for time-ordered requests, responses, retries, or
  success and failure branches;
- use a flowchart for decision logic; and
- use a data model or state diagram when stored structure or transitions are
  the learning objective.

A request/response demo with materially different outcomes should include both
an architecture diagram and a sequence diagram covering the primary success
and failure responses.

Place each diagram beside the narrative it explains: introduce the question or
flow, embed the diagram, then explain the important nodes and arrows in prose.
Keep labels, commands, ports, status codes, and implementation names
synchronized with the runnable capsule. Split a dense diagram rather than
shrinking it into an unreadable overview.

When Mermaid cannot express the diagram clearly, commit the editable source
and an accessible rendered asset. Generated media never replaces the editable
source.

## Multi-language sample applications

Keep the journey and contracts stable while implementations vary:

```text
examples/search/semantic-commerce/
├── example.yaml
├── README.md
├── Makefile
├── contracts/
├── journey/
├── frontend/
├── services/
│   ├── search-python/
│   ├── session-go/
│   └── recommendations-java/
├── deploy/
│   ├── compose.yaml
│   └── providers/
└── tests/
    ├── contract/
    └── end-to-end/
```

Provider overlays are optional adapters and cannot replace the credential-free
local journey.
