# Go

Required structure:

```text
go.mod
go.sum
cmd/                     # when the capsule exposes an executable
internal/                # when implementation packages are useful
*_test.go
```

Requirements:

- declare the supported Go version in `go.mod`;
- commit `go.sum`;
- keep the module self-contained within the capsule;
- format with `gofmt`;
- run `go vet ./...`;
- run `go test ./...`;
- run Staticcheck through a pinned CI installation; and
- use contexts and bounded timeouts for Valkey operations where relevant.

Use a single `main.go` for a genuinely small demo rather than creating empty
package layers.
