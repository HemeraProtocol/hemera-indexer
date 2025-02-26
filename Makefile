ARCH=amd64
VERSION := $(shell grep '^version = ' pyproject.toml | sed 's/^version = //;s/"//g')
BUILD := `git rev-parse --short=7 HEAD`

TAG := $(VERSION)-$(BUILD)-$(ARCH)


PRE_COMMIT_INSTALLED := $(shell command -v pre-commit > /dev/null 2>&1 && echo yes || echo no)
VENV_DIR := .venv
POETRY_INSTALLED := $(shell command -v poetry > /dev/null 2>&1 && echo yes || echo no)

IMAGE_FLAGS := $(IMAGE_FLAGS) --platform linux/$(ARCH)

RED=\033[31m
GREEN=\033[32m
YELLOW=\033[33m
RESET=\033[0m


.PHONY: format init_db development image test

image:
	@echo "Build tag: $(TAG)"
	@echo "Build flags: $(IMAGE_FLAGS)"
	docker buildx build $(IMAGE_FLAGS) --network host -t hemera-protocol:$(TAG) . --no-cache
	@echo "Built image hemera-protocol:$(TAG)"

test:
	@if [ "$(filter-out $@,$(MAKECMDGOALS))" = "" ]; then \
		poetry run pytest -vv; \
	else \
		poetry run pytest -vv -m $(filter-out $@,$(MAKECMDGOALS)); \
	fi


format:
ifeq ($(PRE_COMMIT_INSTALLED),yes)
	@echo "$(YELLOW)Formatting code...$(RESET)"
	@pre-commit run --all-files
else
	@echo "Please install pre-commit in your local machine(pip install pre-commit or brew install pre-commit)"
endif

init_db:
	@echo "Initializing database..."
	poetry run hemera db --init-schema

development:
	@echo "Setting up development environment..."
	@bash -c 'set -euo pipefail; \
	PYTHON_CMD=$$(command -v python3.10 || command -v python.10); \
	if [ -z "$$PYTHON_CMD" ] || ! "$$PYTHON_CMD" --version 2>&1 | grep -q "Python 3"; then \
		echo "Python 3 is not found. Please install Python 3 and try again."; \
		exit 1; \
	fi; \
	python_version=$$($$PYTHON_CMD -c "import sys; print(\"{}.{}\".format(sys.version_info.major, sys.version_info.minor))"); \
	if ! echo "$$python_version" | grep -qE "^3\.(10|11|12|13)"; then \
		echo "Python version $$python_version is not supported. Please use Python 3.10, 3.11, 3.12 or 3.13."; \
		exit 1; \
	fi; \
	echo "Using Python: $$($$PYTHON_CMD --version)"; \
	if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment..."; \
		$$PYTHON_CMD -m venv .venv || { \
			echo "Failed to create virtual environment. Installing venv..."; \
			sudo apt-get update && sudo apt-get install -y python3-venv && $$PYTHON_CMD -m venv .venv; \
		}; \
	fi; \
	echo "Activating virtual environment..."; \
	. .venv/bin/activate; \
	if ! pip --version &> /dev/null; then \
		echo "Installing pip..."; \
		curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py; \
		$$PYTHON_CMD get-pip.py; \
		rm get-pip.py; \
	fi; \
	if ! poetry --version &> /dev/null; then \
		echo "Installing Poetry..."; \
		pip install poetry==1.6.1; \
	else \
		echo "Poetry is already installed."; \
	fi; \
	echo "Installing project dependencies..."; \
	poetry install -v; \
	echo "Development environment setup complete."; \
	echo ""; \
	echo "To activate the virtual environment, run:"; \
	echo "source .venv/bin/activate"'