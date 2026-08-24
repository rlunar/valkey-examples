# Rust

Required structure:

```text
rust-toolchain.toml
Cargo.toml
Cargo.lock
src/
tests/
```

Requirements:

- pin the supported Rust toolchain in `rust-toolchain.toml`;
- commit `Cargo.lock` because capsules are runnable applications;
- format with rustfmt;
- run Clippy with warnings treated as failures;
- run `cargo test --locked`;
- avoid unnecessary unsafe code; and
- document enabled feature flags.

Workspaces are appropriate only when one capsule contains multiple closely
related crates.
