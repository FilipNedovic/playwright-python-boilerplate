import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pytest
import pytest_asyncio
import requests
import structlog
from dotenv import load_dotenv

from src.config.settings import settings

load_dotenv()

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--env",
        action="store",
        default="staging",
        choices=["staging", "production", "development"],
        help="Environment to run tests against",
    )
    parser.addoption("--api-version", action="store", default="v1", help="API version to test")
    parser.addoption("--slow", action="store_true", default=False, help="Run slow tests as well")


def pytest_configure(config):
    """Configure pytest."""
    config.option.allure_report_dir = "reports/allure"

    # Add custom markers
    config.addinivalue_line("markers", "env(name): mark test to run only on named environment")

    # Configure logging based on verbosity
    if config.option.verbose > 0:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on options."""
    env = config.getoption("--env")
    run_slow = config.getoption("--slow")

    skip_slow = pytest.mark.skip(reason="slow test - run with --slow option")
    skip_env = pytest.mark.skip(reason="test only for other environment")

    for item in items:
        # Handle environment markers
        env_marker = item.get_closest_marker("env")
        if env_marker and env_marker.args[0] != env:
            item.add_marker(skip_env)

        # Handle slow tests
        if "slow" in item.keywords and not run_slow:
            item.add_marker(skip_slow)


@pytest_asyncio.fixture
async def api_client(env_config):
    """Provide async API client using httpx.AsyncClient"""
    from src.api.client import APIClient

    client = APIClient(base_url=env_config.get("base_url", ""))

    # Set auth token if configured
    if env_config.get("auth_token"):
        await client.set_auth_token(env_config["auth_token"])

    yield client

    await client.close()


@pytest.fixture
def http_session():
    """Simple HTTP session for quick tests."""
    session = requests.Session()
    session.headers.update({"User-Agent": "Test-Suite/1.0", "Accept": "application/json"})
    yield session
    session.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def env_config(request) -> Dict[str, Any]:
    """Load environment configuration."""
    env = request.config.getoption("--env")

    # Prefer settings/env for values and avoid keeping secrets in source
    def _get_token() -> str | None:
        """Temporary - no authentication needed."""
        return None

    token = _get_token()

    env_urls = {
        "development": "http://localhost:3000",
        "staging": settings.get("api_base_url") or "https://api.staging.example.com",
        "production": settings.get("api_base_url") or "https://api.example.com",
    }

    config = {
        "base_url": env_urls.get(env, settings.get("api_base_url")),
        "api_version": settings.get("api_version") or "v1",
        "auth_token": token,
    }

    config["env"] = env

    # Override with command line options if provided
    cmd_api_version = request.config.getoption("--api-version")
    if cmd_api_version:
        config["api_version"] = cmd_api_version

    logger.info("Environment configured", env=env, base_url=config["base_url"])
    return config


@pytest_asyncio.fixture(scope="session")
async def api_context(env_config):
    """Create Playwright API context."""
    import playwright.async_api

    async with playwright.async_api.async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            base_url=env_config["base_url"],
            extra_http_headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Playwright-API-Tests/1.0",
            },
        )

        # Set default timeout
        context.set_default_timeout(30000)

        yield context

        await context.close()
        await browser.close()


@pytest_asyncio.fixture
async def authenticated_client(api_client):
    """Provide authenticated API client."""
    # This would typically login and set auth token
    # For demo, we'll just set a mock token
    await api_client.set_auth_token("test-jwt-token")
    yield api_client


@pytest.fixture
def test_data():
    """Load test data from fixtures."""

    def load_fixture(fixture_name: str) -> Dict[str, Any]:
        fixture_path = Path(f"data/fixtures/{fixture_name}.json")
        if fixture_path.exists():
            with open(fixture_path) as f:
                return json.load(f)
        return {}

    return load_fixture


@pytest.fixture(autouse=True)
def log_test_execution(request):
    """Automatically log test execution (synchronous to avoid event-loop conflicts)."""
    test_name = request.node.name
    logger.info("Starting test", test=test_name)

    start_time = datetime.now()
    yield

    duration = (datetime.now() - start_time).total_seconds()
    logger.info("Finished test", test=test_name, duration=f"{duration:.2f}s")


# Hook for test failure
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test outcome for reporting."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        logger.error("Test failed", test=item.name, error=str(report.longrepr))


@pytest.fixture
def faker():
    """Provide Faker instance for test data generation."""
    from faker import Faker

    return Faker()
