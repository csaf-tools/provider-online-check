# Development
.SERVICE_TARGETS := frontend backend

$(.SERVICE_TARGETS):
	@echo ""

.FLAGS := no-cache capsule

$(.FLAGS):
	@echo ""

.PHONY: dev

dev dev-help dev-standalone dev-detached dev-attached dev-stop dev-exec dev-enter dev-clean dev-build:
	@bash dev/make-dev.sh $@ "$(filter-out $@, $(MAKECMDGOALS))" "$(ARGS)"

# Service Tests

run-tests:
	PYTHONPATH=backend/ pytest backend/tests/

lint:
	bash dev/run-lint.sh

# DevOps Tests

lint-dockerfiles:
	bash dev/lint-dockerfiles.sh

lint-shell-scripts:
	bash dev/lint-shell-scripts.sh

run-act:
	bash dev/act/run-act.sh
