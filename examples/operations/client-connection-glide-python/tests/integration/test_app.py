"""Run the public application command against real Valkey."""

from __future__ import annotations

import os

import pytest

from valkey_connection.app import main


@pytest.mark.integration
def test_app_prints_the_value_read_from_valkey(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main()

    assert capsys.readouterr().out == f"{os.environ['VALKEY_MESSAGE']}\n"
