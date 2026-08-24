# Swift

Required structure:

```text
.swift-version
Package.swift
Package.resolved
Sources/
Tests/
```

Requirements:

- pin the supported Swift toolchain in `.swift-version`;
- use Swift Package Manager;
- commit `Package.resolved` for runnable capsules;
- keep source and tests in the standard package layout;
- run the repository-approved Swift formatting check;
- run `swift build`; and
- run `swift test`.

Document platform limitations in both `example.yaml` and the capsule README.
