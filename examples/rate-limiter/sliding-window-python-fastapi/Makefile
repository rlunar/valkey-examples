SHELL := /bin/bash
.DEFAULT_GOAL := help

UV_CACHE_DIR ?= $(CURDIR)/.cache/uv
export UV_CACHE_DIR

.PHONY: help setup start stop reset demo format lint typecheck \
	test-unit test-real verify-static verify clean

help:
	@printf '%s\n' \
		"setup        Install the locked Python environment" \
		"start        Start Valkey and the FastAPI application" \
		"stop         Stop only this capsule's resources" \
		"reset        Delete only this capsule's rate-limit keys" \
		"demo         Run the self-cleaning HTTPie journey" \
		"format       Format Python source and tests" \
		"lint         Run Ruff and ShellCheck" \
		"typecheck    Run strict mypy checks" \
		"test-unit    Run tests that do not require Valkey" \
		"test-real    Run integration and journey tests against real Valkey" \
		"verify       Run all static, unit, integration, and journey checks"

setup:
	uv sync --frozen

start:
	./scripts/start.sh

stop:
	./scripts/stop.sh

reset:
	./scripts/reset.sh

demo:
	./scripts/demo.sh

format:
	uv run --frozen ruff format src tests
	uv run --frozen ruff check --fix src tests

lint:
	uv run --frozen ruff format --check src tests
	uv run --frozen ruff check src tests
	@if command -v shellcheck >/dev/null; then shellcheck -x scripts/*.sh tests/shell/*.sh; else echo "shellcheck not installed; skipping shell lint"; fi
	@for test_script in tests/shell/*.sh; do "$$test_script"; done

typecheck:
	uv run --frozen mypy

test-unit:
	uv run --frozen pytest tests/unit

test-real:
	./scripts/test-real.sh

verify-static: lint typecheck
	docker compose config --quiet
	../../../tools/ci/check-structure.sh

verify: setup verify-static test-unit test-real

clean: stop
	rm -rf .artifacts .cache .coverage .pytest_cache .ruff_cache .runtime .venv htmlcov
