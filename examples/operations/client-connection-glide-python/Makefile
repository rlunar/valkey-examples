SHELL := /bin/bash
.DEFAULT_GOAL := help

UV_CACHE_DIR ?= $(CURDIR)/.cache/uv
export UV_CACHE_DIR

.PHONY: help setup start demo reset stop format lint typecheck test-unit \
	test-real verify-static verify

help:
	@printf '%s\n' \
		"setup        Install dependencies and build the app image" \
		"start        Start the topology selected in .env" \
		"demo         Run app.py once and print the stored value" \
		"reset        Delete the one known demo key" \
		"stop         Stop this capsule's Compose resources" \
		"format       Format Python source and tests" \
		"lint         Run Ruff and ShellCheck" \
		"typecheck    Run strict mypy checks" \
		"test-unit    Run tests that do not require Valkey" \
		"test-real    Run app.py against standalone and cluster" \
		"verify       Run every static and behavioral check"

setup:
	test -f .env || cp .env.example .env
	uv sync --frozen
	docker compose build app

start:
	./scripts/start.sh

demo:
	./scripts/demo.sh

reset:
	./scripts/reset.sh

stop:
	./scripts/stop.sh

format:
	uv run --frozen ruff format src tests
	uv run --frozen ruff check --fix src tests

lint:
	uv run --frozen ruff format --check src tests
	uv run --frozen ruff check src tests
	shellcheck -x scripts/*.sh

typecheck:
	uv run --frozen mypy

test-unit:
	uv run --frozen pytest tests/unit --cov --cov-report=term-missing

test-real:
	./scripts/test-real.sh

verify-static: lint typecheck
	docker compose --profile standalone --profile cluster config --quiet
	../../../tools/ci/check-structure.sh

verify: setup verify-static test-unit test-real
