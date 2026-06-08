# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

# Development
.SERVICE_TARGETS := frontend backend

$(.SERVICE_TARGETS):
	@echo ""

.FLAGS := no-cache compose-local-branch

$(.FLAGS):
	@echo ""

.PHONY: dev

dev dev-help dev-standalone dev-detached dev-attached dev-stop dev-exec dev-enter dev-clean dev-build dev-log dev-restart:
	@bash dev/make-dev.sh $@ "$(filter-out $@, $(MAKECMDGOALS))"

# Service Tests

run-tests:
	PYTHONPATH=backend/ pytest --log-cli-level=INFO --timeout=50 backend/tests/

run-tests-containerd:
	make dev-exec backend EXEC_COMMAND="backend pytest --log-cli-level=INFO --timeout=50 tests"

run-fe-tests-containerd:
	make dev-exec frontend EXEC_COMMAND="frontend npm run tests-single"

run-fe-coverage-containerd:
	make dev-exec frontend EXEC_COMMAND="frontend npm run coverage-single"

lint: | lint-reuse
	bash backend/dev/run-lint.sh -l -b

lint-containerd:
	make dev-exec EXEC_COMMAND="backend bash dev/run-lint.sh -l -i"

lint-containerd-standalone:
	bash backend/dev/run-lint.sh

lint-reuse:
	reuse lint

coverage:
	PYTHONPATH=backend/ coverage run -m pytest --log-cli-level=INFO --timeout=50 backend/tests/
	PYTHONPATH=backend/ coverage report -m

coverage-containerd:
	make dev-exec backend EXEC_COMMAND="backend coverage run -m pytest --log-cli-level=INFO --timeout=50 tests"
	make dev-exec backend EXEC_COMMAND="backend coverage report -m"

generate-sboms:
	bash ./dev/sboms/generate-sboms.sh

fe-lint-ci-containerd:
	make dev-exec frontend EXEC_COMMAND="frontend npm run lint-ci"

fe-lint-containerd:
	make dev-exec frontend EXEC_COMMAND="frontend npm run lint"

# CI

ci-coverage:
	make dev-exec backend EXEC_COMMAND="backend coverage run -m pytest --log-cli-level=DEBUG --timeout=15 tests"
	make dev-exec backend EXEC_COMMAND="backend coverage report --fail-under=90"

# CSAF

csaf-check:
	make dev-exec EXEC_COMMAND="backend ./bin/csaf-binary/bin-linux-amd64/csaf_checker --verbose $(SITE)"

# DevOps Tests

lint-dockerfiles:
	bash dev/lint-dockerfiles.sh

lint-shell-scripts:
	bash dev/lint-shell-scripts.sh

run-act:
	bash dev/act/run-act.sh

# Restrict network

restrict-network:
	@bash dev/restrict-network.sh

persist-restrict-network:
	netfilter-persistent save
