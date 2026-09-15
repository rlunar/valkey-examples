# Valkey Deployment Demos

This directory contains the concrete teaching material for the three Valkey
deployment shapes supported by the shared infrastructure capsule:

| Deployment | Demo runbook | Tutorial | Reel script | Tutorial-video script |
| --- | --- | --- | --- | --- |
| Standalone | [`standalone/DEMO.md`](standalone/DEMO.md) | [`standalone/TUTORIAL.md`](standalone/TUTORIAL.md) | [`standalone/SCRIPT_REEL.md`](standalone/SCRIPT_REEL.md) | [`standalone/SCRIPT_VIDEO.md`](standalone/SCRIPT_VIDEO.md) |
| Sentinel-managed replication | [`sentinel/DEMO.md`](sentinel/DEMO.md) | [`sentinel/TUTORIAL.md`](sentinel/TUTORIAL.md) | [`sentinel/SCRIPT_REEL.md`](sentinel/SCRIPT_REEL.md) | [`sentinel/SCRIPT_VIDEO.md`](sentinel/SCRIPT_VIDEO.md) |
| Valkey Cluster | [`cluster/DEMO.md`](cluster/DEMO.md) | [`cluster/TUTORIAL.md`](cluster/TUTORIAL.md) | [`cluster/SCRIPT_REEL.md`](cluster/SCRIPT_REEL.md) | [`cluster/SCRIPT_VIDEO.md`](cluster/SCRIPT_VIDEO.md) |

All three deployments share one [`DESIGN.md`](DESIGN.md). It explains the
common Valkey configuration, Compose profiles, lifecycle interface, topology
differences, and the supporting profiles that are not separate teaching paths.
Each tutorial reproduces the complete Valkey configuration and the
topology-specific Compose definitions it explains, so it can be read without
opening other repository files.

The runbooks assume you have Homebrew, HTTPie, bat, Gum, Glow, jq, and yq.
Each orientation step includes the exact command that renders its Markdown,
source, or configuration context.

Run the documented commands from the `infra/` directory. Each runbook uses a
real deployment and a dedicated Make target:

```shell
make start PROFILE=valkey-standalone
make demo-standalone
make stop
```

Each deployment demo confirms that its containers are running and shows
`PING`, `SET`, `GET`, and selected `INFO` output. The standalone runbook also
compares the host-published plaintext and mutual-TLS profiles with
`make validate-plaintext` and `make validate-tls`.

The Sentinel demo intentionally stops its original primary to prove failover.
Always run `make stop` before repeating it.

Repository-wide templates for authoring example-capsule documentation live in
[`../../docs/templates/`](../../docs/templates/), not in this directory.
