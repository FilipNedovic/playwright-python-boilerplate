import os
from pathlib import Path
from typing import Any, Dict

# Prefer settings from the project's settings module when available
try:
    from src.config.settings import get_base_url, settings
except Exception:
    settings = None
    get_base_url = None


# Helper to resolve base URL
def _resolve_base_url(default: str) -> str:
    if get_base_url:
        try:
            return get_base_url()
        except Exception:
            pass
    if settings and getattr(settings, "API_BASE_URL", None):
        return settings.API_BASE_URL
    return os.getenv("API_BASE_URL", default)


_base_url = _resolve_base_url("https://api.example.com")

# Test timeout: allow env override, otherwise use settings or default
_expect_timeout = int(os.getenv("TEST_TIMEOUT", str(getattr(settings, "TEST_TIMEOUT", 30000) if settings else 30000)))

# Use configurable reporting and trace/video/screenshot behavior
_screenshot = "only-on-failure" if getattr(settings, "SCREENSHOT_ON_FAILURE", True) else "off"
_trace = "retain-on-failure" if getattr(settings, "PLAYWRIGHT_TRACING", False) else "off"
_video = "retain-on-failure" if getattr(settings, "PLAYWRIGHT_TRACING", False) else "off"

# Define the configuration
config: Dict[str, Any] = {
    "base_url": _base_url,
    "api": {
        "timeout": int(os.getenv("API_TIMEOUT", str(getattr(settings, "API_TIMEOUT", 30000) if settings else 30000))),
        "extra_http_headers": {
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    },
    "test": {
        "expect_timeout": _expect_timeout,
        "screenshot": _screenshot,
        "video": _video,
        "trace": _trace,
    },
    "reporter": [
        ["html", {"output_folder": "reports/playwright-html", "open": "never"}],
        ["json", {"output_file": "reports/playwright-report.json"}],
        ["junit", {"output_file": "reports/junit.xml"}],
        ["list"],
    ],
    "projects": [
        {
            "name": "development",
            "use": {"base_url": os.getenv("DEV_API_URL", _base_url)},
        },
        {
            "name": "staging",
            "use": {"base_url": os.getenv("STAGING_API_URL", _base_url)},
        },
        {
            "name": "production",
            "use": {"base_url": os.getenv("PRODUCTION_API_URL", _base_url)},
        },
    ],
}


Path("reports").mkdir(exist_ok=True)
Path("reports/playwright-html").mkdir(exist_ok=True)
Path("reports/screenshots").mkdir(exist_ok=True)
