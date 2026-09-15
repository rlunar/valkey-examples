SHELL := /bin/bash
.DEFAULT_GOAL := help

CAPSULE_ID := sliding-window-python-fastapi
INFRA_ROOT := $(abspath $(CURDIR)/../../..)/infra
CLEAN_PATHS := .artifacts .cache .coverage .mypy_cache .pytest_cache \
	.ruff_cache .runtime .venv htmlcov

include $(INFRA_ROOT)/make/python.mk

.PHONY: help start stop reset demo test-real

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

start:
	./scripts/start.sh

stop:
	./scripts/stop.sh

reset:
	./scripts/reset.sh

demo:
	./scripts/demo.sh

test-real:
	./scripts/test-real.sh
