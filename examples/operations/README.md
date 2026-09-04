# Operations

Examples covering topology, failover, persistence, observability, backup,
restore, scaling, and safe operational behavior belong here.

Standalone operators, CLIs, and benchmark suites belong in purpose-built
repositories.

## Examples

- [Minimal Valkey GLIDE Python connection](client-connection-glide-python/)
  — connects one `app.py` directly to standalone Valkey or a three-primary
  cluster, then runs `SET` and `GET`.
- [Valkey GLIDE Flask client quickstart](client-quickstart-python-flask/)
  — shows the smallest Flask setup for storing and retrieving one value with a
  standalone primary/replica pair or a six-node Valkey Cluster.
- [Topology-aware Flask application with Python and GLIDE](topology-aware-python-flask/)
  — runs one Flask application against standalone, Sentinel, and cluster
  topologies through one small store interface.
