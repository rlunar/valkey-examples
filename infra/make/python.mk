ifndef CAPSULE_ID
$(error CAPSULE_ID must be set before including infra/make/python.mk)
endif

INFRA_ROOT ?= $(abspath $(CURDIR)/../../..)/infra
UV_CACHE_DIR ?= $(CURDIR)/.cache/uv
FORMAT_PATHS ?= src tests
SHELL_SOURCES ?= scripts/*.sh
UNIT_TEST_PATH ?= tests/unit
UNIT_TEST_ARGS ?=
CLEAN_PATHS ?= .cache .coverage .mypy_cache .pytest_cache .ruff_cache .runtime .venv htmlcov

export UV_CACHE_DIR

.PHONY: setup setup-before setup-after format lint typecheck test-unit \
	verify-infra verify-static verify-static-extra verify clean

setup: setup-before
	uv sync --frozen
	@$(MAKE) --no-print-directory setup-after

setup-before setup-after verify-static-extra:

format:
	uv run --frozen ruff format $(FORMAT_PATHS)
	uv run --frozen ruff check --fix $(FORMAT_PATHS)

lint:
	uv run --frozen ruff format --check $(FORMAT_PATHS)
	uv run --frozen ruff check $(FORMAT_PATHS)
	shellcheck -x $(SHELL_SOURCES)

typecheck:
	uv run --frozen mypy

test-unit:
	uv run --frozen pytest $(UNIT_TEST_PATH) $(UNIT_TEST_ARGS)

verify-infra:
	$(MAKE) --no-print-directory -C "$(INFRA_ROOT)" verify
	bash scripts/common.sh config
	../../../tools/ci/check-structure.sh

verify-static: lint typecheck verify-infra verify-static-extra

verify: setup verify-static test-unit test-real

clean: stop
	rm -rf $(CLEAN_PATHS)
