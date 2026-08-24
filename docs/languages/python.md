# Python

Python capsules use uv for runtime selection, dependency locking, and command
execution.

Required structure:

```text
.python-version
pyproject.toml
uv.lock
src/<package>/
tests/
```

Requirements:

- declare the supported Python range in `pyproject.toml`;
- pin the selected interpreter in `.python-version`;
- commit `uv.lock`;
- install with `uv sync --frozen`;
- use a `src/` layout for importable code;
- run Ruff formatting and lint checks;
- run a configured static type checker;
- run tests through `uv run pytest`; and
- execute scripts through `uv run`, not an assumed activated virtual
  environment.

Jupyter cookbooks must keep importable Valkey logic outside the notebook and
execute the notebook in CI.
