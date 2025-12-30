.PHONY: help install install-dev test test-smoke test-regression test-allure \
        test-parallel lint format clean dev

# Colors
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Use the active Python interpreter by default; can be overridden when calling make
PYTHON ?= python

help:
	@echo "$(GREEN)API Testing Framework with Playwright$(NC)"
	@echo ""
	@echo "$(YELLOW)Commands:$(NC)"
	@echo "  $(BLUE)install$(NC)          - Install production dependencies"
	@echo "  $(BLUE)install-dev$(NC)      - Install development dependencies"
	@echo "  $(BLUE)test$(NC)             - Run all tests"
	@echo "  $(BLUE)test-smoke$(NC)       - Run smoke tests"
	@echo "  $(BLUE)test-regression$(NC)  - Run regression tests"
	@echo "  $(BLUE)test-parallel$(NC)    - Run tests in parallel"
	@echo "  $(BLUE)test-allure$(NC)      - Run tests with Allure reporting"
	@echo "  $(BLUE)lint$(NC)             - Run code linting"
	@echo "  $(BLUE)format$(NC)           - Format code with black and isort"
	@echo "  $(BLUE)clean$(NC)            - Clean up generated files"
	@echo "  $(BLUE)dev$(NC)              - Setup development environment"

install:
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	pip install -e .
	python -m playwright install chromium

install-dev: install
	@echo "$(YELLOW)Installing development dependencies...$(NC)"
	pip install -e ".[dev]"
	pre-commit install

test:
	@echo "$(YELLOW)Running all tests...$(NC)"
	pytest tests/ -v --tb=short

test-api:
	@echo "$(YELLOW)Running API tests...$(NC)"
	pytest tests/ -v -m api --tb=short

test-e2e:
	@echo "$(YELLOW)Running E2E tests...$(NC)"
	DEBUG=${DEBUG:=pw:api} pytest ${TEST:-tests/} -v -m e2e --tb=short -s

.PHONY: test-e2e-file
test-e2e-file:
	@echo "$(YELLOW)Running single E2E test (use TEST=path)...$(NC)"
	DEBUG=${DEBUG:=pw:api} pytest ${TEST} -v -s --tb=short

test-smoke:
	@echo "$(YELLOW)Running smoke tests...$(NC)"
	pytest tests/ -v -m smoke --tb=short

test-regression:
	@echo "$(YELLOW)Running regression tests...$(NC)"
	pytest tests/ -v -m regression --tb=short

test-parallel:
	@echo "$(YELLOW)Running tests in parallel...$(NC)"
	pytest tests/ -n auto -v --tb=short

test-html:
	@echo "$(YELLOW)Running tests with HTML report...$(NC)"
	pytest tests/ -v --html=reports/html/report.html --self-contained-html

test-allure:
	@echo "$(YELLOW)Running tests with Allure reporting...$(NC)"
	pytest tests/ -v --alluredir=reports/allure-results
	@echo "$(GREEN)Generating Allure report...$(NC)"
	allure generate reports/allure-results -o reports/allure-report --clean
	@echo "$(GREEN)Report available at: reports/allure-report/index.html$(NC)"

test-env:
	@echo "$(YELLOW)Running tests for specific environment...$(NC)"
	pytest tests/ -v --env=$(env)

lint:
	@echo "$(YELLOW)Running code linting...$(NC)"
	$(PYTHON) -m flake8 tests
	$(PYTHON) -m mypy tests
	$(PYTHON) -m black --check tests
	$(PYTHON) -m isort --check-only tests

format:
	@echo "$(YELLOW)Formatting code...$(NC)"
	black tests
	isort tests


show-python:
	@echo "Makefile PYTHON: $(PYTHON)"
	@echo "Resolved python path: $(shell command -v $(PYTHON) 2>/dev/null || echo not-found)"
	@$(PYTHON) --version || true
	@$(PYTHON) -m flake8 --version || true


clean:
	@echo "$(YELLOW)Cleaning up...$(NC)"
	rm -rf reports/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf __pycache__/
	rm -rf */__pycache__/
	rm -rf */*/__pycache__/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

dev: install-dev format
	@echo "$(GREEN)Development environment ready!$(NC)"
