SHELL := /bin/bash
.DEFAULT_GOAL := help

UV_CACHE_DIR ?= $(CURDIR)/.cache/uv
export UV_CACHE_DIR

.PHONY: help setup start stop reset demo format lint typecheck test-unit \
	test-real verify-static verify clean

help:
	@printf '%s\n' \
		"setup        Install the locked Python environment" \
		"start        Start TOPOLOGY=standalone|sentinel|cluster (default: standalone)" \
		"stop         Stop only this capsule's Compose resources" \
		"reset        Delete the known demo counter through the application" \
		"demo         Exercise topology reporting and the demo counter" \
		"format       Format Python source and tests" \
		"lint         Run Ruff and ShellCheck" \
		"typecheck    Run strict mypy checks" \
		"test-unit    Run tests that do not require Valkey" \
		"test-real    Run integration and HTTP journeys against all topologies" \
		"verify       Run all static, unit, integration, and journey checks"

setup:
	uv sync --frozen

start:
	./scripts/start.sh

stop:
	./scripts/stop.sh

reset:
	uv run --frozen python scripts/reset.py

demo:
	uv run --frozen python scripts/demo.py

format:
	uv run --frozen ruff format src tests scripts
	uv run --frozen ruff check --fix src tests scripts

lint:
	uv run --frozen ruff format --check src tests scripts
	uv run --frozen ruff check src tests scripts
	shellcheck -x scripts/*.sh

typecheck:
	uv run --frozen mypy

test-unit:
	uv run --frozen pytest tests/unit --cov --cov-report=term-missing

test-real:
	./scripts/test-real.sh

verify-static: lint typecheck
	docker compose config --quiet
	../../../tools/ci/check-structure.sh

verify: setup verify-static test-unit test-real

clean: stop
	rm -rf .cache .coverage .mypy_cache .pytest_cache .ruff_cache .runtime .venv \
		htmlcov src/*.egg-info
