.PHONY: help install install-dev test test-api test-e2e test-e2e-file \
        test-smoke test-regression test-parallel test-html test-allure \
        test-env lint format show-python clean dev fresh nuke

# ============================================================================
# COLOR DEFINITIONS
# ============================================================================
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m  # No Color

# ============================================================================
# CONFIGURATION
# ============================================================================
# Use the active Python interpreter by default; can be overridden when calling make
# Example: PYTHON=python3.12 make test
PYTHON ?= python

# ============================================================================
# HELP TARGET
# ============================================================================
help:
	@echo "$(GREEN)API Testing Framework with Playwright$(NC)"
	@echo ""
	@echo "$(YELLOW)Commands:$(NC)"
	@echo "  $(BLUE)install$(NC)          - Install production dependencies"
	@echo "  $(BLUE)install-dev$(NC)      - Install development dependencies"
	@echo "  $(BLUE)test$(NC)             - Run all tests"
	@echo "  $(BLUE)test-api$(NC)         - Run API tests only"
	@echo "  $(BLUE)test-e2e$(NC)         - Run E2E tests only"
	@echo "  $(BLUE)test-smoke$(NC)       - Run smoke tests"
	@echo "  $(BLUE)test-regression$(NC)  - Run regression tests"
	@echo "  $(BLUE)test-parallel$(NC)    - Run tests in parallel"
	@echo "  $(BLUE)test-allure$(NC)      - Run tests with Allure reporting"
	@echo "  $(BLUE)lint$(NC)             - Run code linting"
	@echo "  $(BLUE)format$(NC)           - Format code with black and isort"
	@echo "  $(BLUE)clean$(NC)            - Clean up generated files"
	@echo "  $(BLUE)dev$(NC)              - Setup development environment"
	@echo "  $(BLUE)fresh$(NC)            - Fresh install (cleans venv + reinstalls)"
	@echo "  $(BLUE)nuke$(NC)             - Delete everything (venv, caches, reports)"

# ============================================================================
# INSTALLATION TARGETS
# ============================================================================
install:
	@echo "$(YELLOW)Installing production dependencies...$(NC)"
	pip install -e .
	@echo "$(YELLOW)Installing Playwright browsers...$(NC)"
	python -m playwright install chromium

install-dev: install
	@echo "$(YELLOW)Installing development dependencies...$(NC)"
	pip install -e ".[dev]"
	pre-commit install

# ============================================================================
# TESTING TARGETS
# ============================================================================
test:
	@echo "$(YELLOW)Running all tests...$(NC)"
	pytest tests/ -v --tb=short

test-api:
	@echo "$(YELLOW)Running API tests...$(NC)"
	pytest tests/ -v -m api --tb=short

# Note: DEBUG environment variable enables Playwright debug output
# TEST variable can be used to run specific tests
test-e2e:
	@echo "$(YELLOW)Running E2E tests...$(NC)"
	DEBUG=${DEBUG:=pw:api} pytest ${TEST:-tests/} -v -m e2e --tb=short -s

# Usage: make test-e2e-file TEST=tests/e2e/test_login.py
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

# Usage: make test-env env=staging
test-env:
	@echo "$(YELLOW)Running tests for $(env) environment...$(NC)"
	pytest tests/ -v --env=$(env)

# ============================================================================
# CODE QUALITY TARGETS
# ============================================================================
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

# ============================================================================
# DEBUG/DIAGNOSTIC TARGETS
# ============================================================================
show-python:
	@echo "Makefile PYTHON variable: $(PYTHON)"
	@echo "Resolved python path: $(shell command -v $(PYTHON) 2>/dev/null || echo not-found)"
	@$(PYTHON) --version || true
	@$(PYTHON) -m flake8 --version || true

# ============================================================================
# CLEANUP TARGETS
# ============================================================================
clean:
	@echo "$(YELLOW)Cleaning up generated files...$(NC)"
	rm -rf reports/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf __pycache__/
	rm -rf */__pycache__/
	rm -rf */*/__pycache__/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	rm -rf build/ dist/ .eggs/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "$(GREEN)✅ Clean complete$(NC)"

# Development environment setup
dev: install-dev format
	@echo "$(GREEN)Development environment ready!$(NC)"

# Fresh install - cleans venv and reinstalls everything
fresh: clean
	@echo "$(YELLOW)🔄 Creating fresh environment...$(NC)"
	@echo "$(YELLOW)Deactivating current venv if active...$(NC)"
	deactivate 2>/dev/null || true
	rm -rf venv/
	python -m venv venv
	@echo "$(GREEN)✅ Virtual environment created$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  source venv/bin/activate                 # Linux/macOS"
	@echo "  venv\Scripts\activate                   # Windows"
	@echo "  pip install -e .[dev]                   # Install dependencies"

# Nuclear option - deletes everything including Playwright browsers
nuke: clean
	@echo "$(RED)💥 Deleting everything (nuclear option)...$(NC)"
	rm -rf venv/ .venv/ .playwright/
	@echo "$(GREEN)✅ Everything deleted. Start fresh with 'make fresh'$(NC)"

# ============================================================================
# NOTES:
# ============================================================================
# 1. The 'test-e2e' target uses DEBUG=${DEBUG:=pw:api} which sets a default
#    debug level for Playwright. You can override it:
#    DEBUG=pw:api,pw:browser make test-e2e
#
# 2. The 'test-e2e-file' target requires TEST variable:
#    make test-e2e-file TEST=tests/e2e/test_login.py
#
# 3. Colors may not work in all terminals. Remove color definitions if issues.
#
# 4. 'pip install -e .' installs in development mode (editable).
#    Use 'pip install .' for regular installation.
#
# 5. The 'clean' target does NOT delete virtual environments by default.
#    Use 'make fresh' or 'make nuke' for that.
