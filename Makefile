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
	@echo "Built image hemera-protocol:$(VERSION)-$(BUILD)"

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
	poetry run python -m hemera.py init_db

.PHONY: development

development:
	@echo "Setting up development environment..."
	@if ! command -v python3 &> /dev/null; then \
		echo "Python 3 is not installed. Please install Python 3 and try again."; \
		exit 1; \
	fi
	@python_version=$$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))'); \
	if ! echo "$$python_version" | grep -qE '^3\.(8|9|10|11)'; then \
		echo "Python version $$python_version is not supported. Please use Python 3.8, 3.9, 3.10, or 3.11."; \
		exit 1; \
	fi
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv .venv; \
	fi
	@echo "Activating virtual environment..."
	@. .venv/bin/activate && \
	if ! command -v pip &> /dev/null; then \
		echo "Installing pip..."; \
		curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py; \
		python3 get-pip.py; \
		rm get-pip.py; \
	fi && \
	if ! command -v poetry &> /dev/null; then \
		echo "Installing Poetry..."; \
		pip install poetry; \
	else \
		echo "Poetry is already installed."; \
	fi && \
	echo "Installing project dependencies..." && \
	poetry install -v && \
	echo "Development environment setup complete." && \
	echo "" && \
	echo "To activate the virtual environment, run:" && \
	echo "source .venv/bin/activate"

