# Minimal Valkey GLIDE 30-Second Runbook

## Goal

Record one topology per take. You should show:

1. dotenv configuration;
2. the standalone or cluster GLIDE constructor;
3. `SET` and `GET`; and
4. the value printed from real Valkey.

## Prepare before recording

For standalone, keep the default `.env`:

```dotenv
VALKEY_MODE=standalone
VALKEY_ADDRESSES=standalone:6379
VALKEY_MESSAGE=hello from GLIDE
```

Prepare dependencies and start Valkey before the take:

```shell
make setup
make start
```

Confirm the selected services:

```shell
yq '.services | keys' compose.yaml
yq '.services | keys' ../../../infra/compose.yaml
source scripts/common.sh
compose ps
```

## Record the 30-second take

### 0-12 seconds: show the whole application

```shell
gum style --bold "GLIDE connection, SET, GET, and cleanup"
bat --paging=never --style=numbers \
  --highlight-line 23:36 \
  --highlight-line 39:59 \
  src/valkey_connection/app.py
```

Suggested narration:

> Dotenv loads the mode and addresses. We create a normal GLIDE client or a
> cluster client, then use the same SET and GET calls.

### 12-25 seconds: run it

```shell
make demo
```

Expected output:

```text
hello from GLIDE
```

Suggested narration:

> The application wrote that value to Valkey, read it back, decoded it, and
> printed it.

### 25-30 seconds: close

Display the cleanup lines:

```shell
gum style --bold "Always close the client"
bat --paging=never --style=numbers \
  --highlight-line 55:59 \
  src/valkey_connection/app.py
```

Finish with:

> One file, one client, and the same commands for standalone or cluster.

## Cluster take

Stop standalone:

```shell
make stop
```

Change `.env`:

```dotenv
VALKEY_MODE=cluster
VALKEY_ADDRESSES=cluster-node-1:6379,cluster-node-2:6379,cluster-node-3:6379
VALKEY_MESSAGE=hello from GLIDE
```

Prepare the cluster before recording:

```shell
make start
```

Record the same `bat` and `make demo` commands. The output remains:

```text
hello from GLIDE
```

The only code path that changes is the constructor selected by
`VALKEY_MODE`.

## After recording

```shell
make reset
make stop
```

Run the full pre-publication check:

```shell
make verify
```

## Recovery

Inspect the selected topology:

```shell
source scripts/common.sh
TOPOLOGY=standalone compose ps
TOPOLOGY=cluster compose ps
```

Inspect Valkey logs:

```shell
source scripts/common.sh
TOPOLOGY=standalone compose logs --tail=100 standalone
TOPOLOGY=cluster compose logs --tail=100 cluster-node-1
```

Remove only this capsule's resources:

```shell
make stop
```
