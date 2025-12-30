# Playwright Python Boilerplate

This repository is a lightweight boilerplate for API and E2E tests using Playwright and pytest.

Quick start

1. Create a virtual environment and activate it:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies (includes dev extras):

```bash
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

3. Install Playwright browsers:

```bash
python -m playwright install --with-deps
```

4. Run tests:

```bash
pytest -v
```

5. Generate HTML / Allure reports (pytest options used in `pytest.ini`):

```bash
pytest --html=reports/html/report.html --self-contained-html --alluredir=reports/allure
```

Developer tools

- Install pre-commit hooks:

```bash
pre-commit install
pre-commit run --all-files
```

Notes

- Settings are in `src/config/settings.py` and can be overridden with an `.env` file or environment variables.
- The async API client uses `httpx.AsyncClient`; fixtures in `conftest.py` are async-aware.
- CI workflow is provided in `.github/workflows/ci.yml`.

Makefile quick start

If you have `make` available you can use the included Makefile for convenience. Examples:

```bash
# Install dependencies (including dev extras) and pre-commit hooks
make install-dev

# Install Playwright browsers (if not done by install step)
python -m playwright install --with-deps

# Run all tests
make test

# Run E2E tests using pytest-playwright plugin
make test-e2e

# Run lint using the venv's python (recommended)
PYTHON=$(which python) make lint
```

Notes:
- Use `PYTHON=$(which python)` when invoking `make` if you want the Makefile to use your active virtualenv's interpreter.
- The README quick start still lists explicit `python -m ...` commands for portability on systems without `make` (Windows without WSL).
