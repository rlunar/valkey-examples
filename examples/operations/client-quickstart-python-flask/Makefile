SHELL := /bin/bash
.DEFAULT_GOAL := help

CAPSULE_ID := client-quickstart-python-flask
INFRA_ROOT := $(abspath $(CURDIR)/../../..)/infra
FORMAT_PATHS := src tests scripts
UNIT_TEST_ARGS := --cov --cov-report=term-missing

include $(INFRA_ROOT)/make/python.mk

.PHONY: help start stop reset demo test-real

help:
	@printf '%s\n' \
		"setup        Install the locked Python environment" \
		"start        Start TOPOLOGY=standalone|cluster (default: standalone)" \
		"stop         Stop this capsule's Compose resources" \
		"reset        Delete the one known demo key" \
		"demo         Store and retrieve a value through Flask" \
		"format       Format Python source and tests" \
		"lint         Run Ruff and ShellCheck" \
		"typecheck    Run strict mypy checks" \
		"test-unit    Run tests that do not require Valkey" \
		"test-real    Run integration and HTTP journeys against both topologies" \
		"verify       Run every static and behavioral check"

start:
	./scripts/start.sh

stop:
	./scripts/stop.sh

reset:
	uv run --frozen python scripts/reset.py

demo:
	uv run --frozen python scripts/demo.py

test-real:
	./scripts/test-real.sh
