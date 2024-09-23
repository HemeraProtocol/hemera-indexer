VERSION := $(shell poetry version -s)
BUILD := `git rev-parse --short=7 HEAD`
SERVICES =
.PHONY: all build image test

RED=\033[31m
GREEN=\033[32m
YELLOW=\033[33m
RESET=\033[0m

image:

	docker build $(IMAGE_FLAGS) --network host -t hemera-protocol:$(VERSION)-$(BUILD) . --no-cache
	echo "Built image hemera-protocol:$(VERSION)-$(BUILD)"

test:
	@if [ "$(filter-out $@,$(MAKECMDGOALS))" = "" ]; then \
		poetry run pytest -vv; \
	else \
		poetry run pytest -vv -m $(filter-out $@,$(MAKECMDGOALS)); \
	fi

PRE_COMMIT_INSTALLED := $(shell command -v pre-commit > /dev/null 2>&1 && echo yes || echo no)

format:
ifeq ($(PRE_COMMIT_INSTALLED),yes)
	@echo "$(YELLOW)Formatting code...$(RESET)"
	@pre-commit run --all-files
else
	@echo "Please install pre-commit in your local machine(pip install pre-commit or brew install pre-commit)"
endif

init_db:
	@echo "Initializing database..."
	python -m hemera.py init_db