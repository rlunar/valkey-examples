SHELL := /bin/bash
.DEFAULT_GOAL := help

PROFILE ?= valkey-standalone-host
CAPSULE_ID ?= shared-infra
COMPOSE_PROJECT_NAME ?= valkey-example-$(CAPSULE_ID)
TLS_CERT_DIR ?= $(CURDIR)/.cache/tls
CAPSULE ?=
INFRA_PROFILES := \
	valkey-standalone \
	valkey-standalone-replicated \
	valkey-sentinel \
	valkey-cluster-3 \
	valkey-cluster-6 \
	valkey-standalone-host \
	valkey-standalone-tls-host \
	postgres
ALL_PROFILE_ARGS := $(foreach profile,$(INFRA_PROFILES),--profile "$(profile)")

export CAPSULE_ID
export COMPOSE_PROJECT_NAME
export INFRA_ROOT := $(CURDIR)
export TLS_CERT_DIR

.PHONY: help setup docs-init tls-setup tls-ping tls-clean start \
	validate-plaintext validate-tls demo-standalone demo-sentinel \
	demo-cluster verify test-real reset stop

help:
	@printf '%s\n' \
		"setup        Check Docker and Compose availability" \
		"docs-init    Create missing demo, tutorial, and video docs for CAPSULE=..." \
		"start        Start PROFILE=$(PROFILE)" \
		"validate-plaintext  Check container, PING, SET/GET, and INFO without TLS" \
		"validate-tls        Check container, PING, SET/GET, and INFO with mutual TLS" \
		"demo-standalone  Demonstrate one standalone Valkey node" \
		"demo-sentinel    Demonstrate Sentinel discovery and failover" \
		"demo-cluster     Demonstrate a three-primary Valkey Cluster" \
		"tls-setup    Generate ignored local CA, server, and client certificates" \
		"tls-ping     Ping the running mutual-TLS Valkey profile" \
		"tls-clean    Remove generated local TLS material" \
		"verify       Validate Compose, shared scripts, and wrapper tests" \
		"test-real    Test transport validation and all topologies against real Valkey" \
		"reset        Remove this project's containers and ephemeral data" \
		"stop         Stop this project's resources"

setup:
	@command -v docker >/dev/null
	@docker compose version >/dev/null

docs-init:
	@test -n "$(CAPSULE)" || { \
		echo "CAPSULE is required: make docs-init CAPSULE=examples/<capability>/<capsule>" >&2; \
		exit 2; \
	}
	./scripts/scaffold-docs.sh "$(CAPSULE)"

start: setup
	@if [[ "$(PROFILE)" == *tls* ]]; then \
		"$(CURDIR)/scripts/generate-tls-certs.sh" "$(TLS_CERT_DIR)"; \
	fi
	docker compose --profile "$(PROFILE)" up -d --wait

validate-plaintext: setup
	./scripts/validate-valkey.sh plaintext

validate-tls: setup
	./scripts/validate-valkey.sh tls

demo-standalone: setup
	./scripts/demo-deployment.sh standalone

demo-sentinel: setup
	./scripts/demo-deployment.sh sentinel

demo-cluster: setup
	./scripts/demo-deployment.sh cluster

tls-setup:
	./scripts/generate-tls-certs.sh "$(TLS_CERT_DIR)"

tls-ping: tls-setup
	docker compose --profile valkey-standalone-tls-host exec -T valkey-tls \
		valkey-cli \
		--tls \
		--cacert /tls/ca.crt \
		--cert /tls/client.crt \
		--key /tls/client.key \
		-h 127.0.0.1 \
		-p 6379 \
		ping

tls-clean:
	rm -rf "$(TLS_CERT_DIR)"

verify:
	docker compose $(ALL_PROFILE_ARGS) config --quiet
	shellcheck -x scripts/*.sh tests/*.sh
	python3 -c 'from pathlib import Path; compile(Path("scripts/wait_for_http.py").read_text(), "scripts/wait_for_http.py", "exec")'
	@set -e; for test_script in tests/test-*-shared.sh; do "$$test_script"; done

test-real: setup
	./tests/test-infra-real.sh
	./tests/test-deployment-demos-real.sh

reset:
	docker compose $(ALL_PROFILE_ARGS) down --remove-orphans --volumes

stop:
	docker compose $(ALL_PROFILE_ARGS) down --remove-orphans
