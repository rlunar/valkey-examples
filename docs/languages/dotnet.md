# .NET and C Sharp

Required structure:

```text
global.json
Directory.Build.props
src/<Project>/<Project>.csproj
tests/<Project>.Tests/<Project>.Tests.csproj
packages.lock.json
```

Requirements:

- pin the .NET SDK and roll-forward policy in `global.json`;
- centralize shared compiler settings in `Directory.Build.props`;
- enable nullable reference types and implicit usings where appropriate;
- commit NuGet lockfiles;
- restore with locked mode;
- run `dotnet format --verify-no-changes`;
- build with warnings treated as errors; and
- run `dotnet test`.

A very small demo may use one project, but source and tests must remain
separable.
