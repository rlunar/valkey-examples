from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from rate_limiter_demo.config import AppConfig


def test_defaults_to_multi_exec(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "RATE_LIMIT_IMPLEMENTATION",
        "RATE_LIMIT_REQUESTS",
        "RATE_LIMIT_WINDOW_MS",
    ):
        monkeypatch.delenv(name, raising=False)

    config = AppConfig(_env_file=None)

    assert config.implementation == "multi-exec"
    assert config.request_limit == 5
    assert config.window_ms == 10_000


def test_reads_lua_policy_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_IMPLEMENTATION", "lua")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "17")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_MS", "2500")

    config = AppConfig(_env_file=None)

    assert config.implementation == "lua"
    assert config.request_limit == 17
    assert config.window_ms == 2_500


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("RATE_LIMIT_IMPLEMENTATION", "pipeline"),
        ("RATE_LIMIT_REQUESTS", "zero"),
        ("RATE_LIMIT_REQUESTS", "0"),
        ("RATE_LIMIT_WINDOW_MS", "99"),
    ],
)
def test_rejects_invalid_environment(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValidationError) as raised:
        AppConfig(_env_file=None)

    assert raised.value.errors()[0]["loc"] == (name,)


def test_rejects_invalid_policy_slug() -> None:
    with pytest.raises(ValidationError):
        AppConfig(policy_id="Not Valid", _env_file=None)


def test_environment_takes_precedence_over_dotenv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text("RATE_LIMIT_REQUESTS=7\n", encoding="utf-8")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "9")

    config = AppConfig(_env_file=dotenv)

    assert config.request_limit == 9


def test_is_immutable() -> None:
    config = AppConfig(_env_file=None)

    with pytest.raises(ValidationError):
        config.request_limit = 10
