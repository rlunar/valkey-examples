# Valkey Examples

Valkey Examples is a curated catalog of runnable educational code that makes
Valkey behavior observable from a clean clone.

The repository is organized by Valkey capability rather than by framework,
vendor, or programming language. Each example capsule owns its dependencies,
lockfiles, application code, tests, ownership, and lifecycle interface. A
single root [infrastructure capsule](infra/) owns the repeated local Valkey and
PostgreSQL processes, shared Valkey tuning, an opt-in mutual-TLS profile, and
the Make and Bash orchestration around them.

> [!IMPORTANT]
> This repository contains educational examples, not certified production
> architectures. Review each example's documented security and operational
> limitations before adapting it for production.

## Repository status

The repository is currently in its bootstrap phase. Policy, schemas, authoring
guidance, and structural validation are present, but no example is part of the
maintained catalog yet.

Runnable examples must not be admitted until:

- repository maintainers and language reviewers are named;
- the supported Valkey and language-version matrix is approved;
- manifest-driven runtime and compatibility CI is enabled;
- security, dependency, image, secret, and license scans are blocking; and
- an uninvolved reviewer reproduces the documented journey from a clean clone.

See [MAINTAINERS.md](MAINTAINERS.md) and
[COMPATIBILITY.md](COMPATIBILITY.md) for the remaining launch decisions.
Candidate designs are tracked in [docs/proposals](docs/proposals/README.md)
before implementation begins.

## Scope

The catalog accepts exactly three kinds of example:

- **Cookbook:** a guided sequence with executable steps and a core path that
  completes within 15 minutes.
- **Demo:** the smallest complete program that demonstrates one primary Valkey
  capability and produces visible output within five minutes.
- **Sample application:** a coherent user journey combining multiple Valkey
  capabilities, with architecture documentation and end-to-end tests.

Tools, libraries, operators, actions, benchmark suites, event assets, and
projects requiring independent releases or security advisories belong in
purpose-built repositories.

## Learning levels

Every capsule declares one learner level in `example.yaml`:

| Level | Audience |
| --- | --- |
| `L100` | Beginner |
| `L200` | Intermediate |
| `L300` | Advanced |
| `L400` | Expert |
| `L500` | Maintainer |

The level describes prerequisite knowledge and conceptual depth, not code size,
container count, or resource requirements. The complete definitions and
classification guidance are in [docs/authoring.md](docs/authoring.md).

## Suggested learning order

These capsules build on one another:

| Step | Capsule | Main idea |
| --- | --- | --- |
| 1 | [Minimal GLIDE connection](examples/operations/client-connection-glide-python/) | Connect, `SET`, `GET`, and close |
| 2 | [Flask client quickstart](examples/operations/client-quickstart-python-flask/) | Put the same commands behind one HTTP route |
| 3 | [Validated object storage](examples/data-structures/validated-object-storage-python-flask/) | Check an object, store JSON, and rebuild its type |
| 4 | [Topology-aware Flask](examples/operations/topology-aware-python-flask/) | Keep route code unchanged across standalone, Sentinel, and cluster |
| 5 | [Flask rate limiter](examples/rate-limiter/sliding-window-python-flask/) | Use a sorted set and transaction to limit requests |
| 6 | [FastAPI rate limiter](examples/rate-limiter/sliding-window-python-fastapi/) | Run the same limiter with asynchronous Python |

Start with the [infrastructure standalone
tutorial](infra/docs/standalone/TUTORIAL.md) if Docker or Valkey server setup
is new to you.

## Structure

```text
.
├── .github/                  # contribution routing and repository workflows
├── catalog/                  # generated catalog outputs
├── docs/
│   ├── authoring.md
│   ├── languages/            # ecosystem-specific authoring requirements
│   └── templates/            # demo, tutorial, and video authoring templates
├── examples/
│   ├── caching/
│   ├── data-structures/
│   ├── messaging-and-streams/
│   ├── migrations-and-integrations/
│   ├── operations/
│   ├── rate-limiter/
│   └── search/
├── infra/                    # shared databases, lifecycle, and deployment demos
├── schemas/                  # manifest and compatibility contracts
└── tools/                    # metadata, catalog, and CI tooling only
```

The example kind, level, language, owners, compatibility, and lifecycle are
metadata. They are exposed as filters in the generated catalog rather than
duplicated as top-level directory hierarchies.

## Example capsule

A typical single-language capsule looks like this:

```text
examples/<capability>/<slug>-<language>/
├── example.yaml
├── README.md
├── Makefile
├── compose.yaml              # app-only services, when the app is containerized
├── .env.example              # variable names and safe placeholders only
├── docs/
│   ├── DEMO.md
│   ├── TUTORIAL.md
│   ├── SCRIPT_REEL.md
│   ├── SCRIPT_VIDEO.md
│   └── VIDEO.md
├── src/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── journey/
├── data/                     # deterministic fixtures, when required
├── expected/                 # snapshots or assertions, when useful
└── THIRD_PARTY.md            # external data, dependency, or model notices
```

Directories that are not needed are omitted rather than committed empty.

Every capsule exposes the same small interface:

```shell
make setup
make start
make verify
make reset
make stop
```

These targets delegate to the language's native tools and the shared
`infra/` capsule. Capsules must not import a repository-local application
runtime library or depend on another example capsule. Their `example.yaml`
must point to `../../../infra` and list the exact infrastructure profiles used
by the journey.

## Language tooling

Each capsule owns its language version declaration, project manifest, lockfile,
source layout, and tests. Current authoring profiles are documented for:

- [Python with uv](docs/languages/python.md)
- [TypeScript and Node.js with nvm and npm](docs/languages/typescript.md)
- [Java and Kotlin with the Gradle Wrapper](docs/languages/java-kotlin.md)
- [Go](docs/languages/go.md)
- [Rust](docs/languages/rust.md)
- [.NET and C#](docs/languages/dotnet.md)
- [PHP](docs/languages/php.md)
- [Ruby](docs/languages/ruby.md)
- [Swift](docs/languages/swift.md)

A language may be documented before it has a catalog entry, but an example in
that language cannot be maintained until primary and backup reviewers exist.

## Adding an example

Start with the proposal issue form. Do not begin by opening a large
implementation pull request.

The proposal must identify:

- the Valkey behavior and expected observable result;
- cookbook, demo, or sample-application kind;
- L100–L500 learning level;
- capability category and proposed capsule path;
- language, client, Valkey, and dependency versions;
- credential-free local journey and resource budget;
- primary and backup content owners;
- primary and backup language or domain reviewers;
- security considerations and production limitations; and
- the archive or migration destination if the capsule leaves this repository.

The complete process and placement test are in
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

Repository-authored content is licensed under the [MIT License](LICENSE).
Third-party code, data, and model artifacts retain their original licenses and
must be documented within the affected capsule.
