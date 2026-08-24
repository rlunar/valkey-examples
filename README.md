# Valkey Examples

Valkey Examples is a curated catalog of runnable educational code that makes
Valkey behavior observable from a clean clone.

The repository is organized by Valkey capability rather than by framework,
vendor, or programming language. Each independently runnable directory is an
example capsule with its own dependencies, lockfiles, tests, ownership, and
lifecycle.

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

## Structure

```text
.
├── .github/                  # contribution routing and repository workflows
├── catalog/                  # generated catalog outputs
├── docs/
│   ├── authoring.md
│   └── languages/            # ecosystem-specific authoring requirements
├── examples/
│   ├── caching/
│   ├── data-structures/
│   ├── messaging-and-streams/
│   ├── migrations-and-integrations/
│   ├── operations/
│   ├── rate-limiter/
│   └── search/
├── schemas/                  # manifest and compatibility contracts
└── tools/                    # metadata, catalog, and CI tooling only
```

The example kind, language, owners, compatibility, and lifecycle are metadata.
They are exposed as filters in the generated catalog rather than duplicated as
top-level directory hierarchies.

## Example capsule

A typical single-language capsule looks like this:

```text
examples/<capability>/<slug>-<language>/
├── example.yaml
├── README.md
├── Makefile
├── compose.yaml              # only when multiple processes are required
├── .env.example              # variable names and safe placeholders only
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

These targets delegate to the language's native tools. Capsules must not import
a repository-local runtime library or depend on another capsule.

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
