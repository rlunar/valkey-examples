from __future__ import annotations

import pytest

from rate_limiter_demo.config import AppConfig, ConfigurationError


def test_defaults_to_multi_exec(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "RATE_LIMIT_IMPLEMENTATION",
        "RATE_LIMIT_REQUESTS",
        "RATE_LIMIT_WINDOW_MS",
    ):
        monkeypatch.delenv(name, raising=False)

    config = AppConfig.from_env()

    assert config.implementation == "multi-exec"
    assert config.request_limit == 5
    assert config.window_ms == 10_000


def test_reads_lua_policy_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_IMPLEMENTATION", "lua")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "17")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_MS", "2500")

    config = AppConfig.from_env()

    assert config.implementation == "lua"
    assert config.request_limit == 17
    assert config.window_ms == 2_500


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("RATE_LIMIT_IMPLEMENTATION", "pipeline", "multi-exec"),
        ("RATE_LIMIT_REQUESTS", "zero", "integer"),
        ("RATE_LIMIT_REQUESTS", "0", "between"),
        ("RATE_LIMIT_WINDOW_MS", "99", "between"),
    ],
)
def test_rejects_invalid_environment(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str, message: str
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ConfigurationError, match=message):
        AppConfig.from_env()


def test_rejects_invalid_policy_slug() -> None:
    with pytest.raises(ConfigurationError, match="lowercase slug"):
        AppConfig(policy_id="Not Valid")
