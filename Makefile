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

lint:
	bash backend/dev/run-lint.sh -l /backend

lint-containerd:
	bash backend/dev/run-lint.sh

# DevOps Tests

lint-dockerfiles:
	bash dev/lint-dockerfiles.sh

lint-shell-scripts:
	bash dev/lint-shell-scripts.sh

run-act:
	bash dev/act/run-act.sh
