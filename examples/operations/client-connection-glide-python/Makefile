SHELL := /bin/bash
.DEFAULT_GOAL := help

CAPSULE_ID := client-connection-glide-python
INFRA_ROOT := $(abspath $(CURDIR)/../../..)/infra
UNIT_TEST_ARGS := --cov --cov-report=term-missing

include $(INFRA_ROOT)/make/python.mk

.PHONY: help start demo reset stop test-real

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

setup-before:
	test -f .env || cp .env.example .env

setup-after:
	@bash -c 'source scripts/common.sh; compose build app'

start:
	./scripts/start.sh

demo:
	./scripts/demo.sh

reset:
	./scripts/reset.sh

stop:
	./scripts/stop.sh

test-real:
	./scripts/test-real.sh
