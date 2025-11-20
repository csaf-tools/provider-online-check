# Development
.SERVICE_TARGETS := frontend backend

$(.SERVICE_TARGETS):
	@echo ""

.FLAGS := no-cache capsule compose-local-branch

$(.FLAGS):
	@echo ""

.PHONY: dev

dev dev-help dev-standalone dev-detached dev-attached dev-stop dev-exec dev-enter dev-clean dev-build dev-log dev-restart:
	@bash dev/make-dev.sh $@ "$(filter-out $@, $(MAKECMDGOALS))"

# Service Tests

run-tests:
	PYTHONPATH=backend/ pytest backend/tests/

run-tests-containerd:
	make dev-exec backend EXEC_COMMAND="backend pytest tests"

lint:
	bash backend/dev/run-lint.sh -l -b

lint-containerd:
	make dev-exec "backend bash dev/run-lint.sh -l -i"

lint-containerd-standalone:
	bash backend/dev/run-lint.sh

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
