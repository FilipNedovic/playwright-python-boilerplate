import os

from dotenv import load_dotenv

load_dotenv()

# Simple settings as a dictionary
settings = {
    # Environment
    "environment": os.getenv("ENVIRONMENT", "staging"),
    # API Settings
    "api_base_url": os.getenv("API_BASE_URL", "https://api.staging.example.com"),
    "api_version": os.getenv("API_VERSION", "v1"),
    "api_timeout": int(os.getenv("API_TIMEOUT", "30000")),
    "api_max_retries": int(os.getenv("API_MAX_RETRIES", "3")),
    # Authentication
    "auth_token": os.getenv("AUTH_TOKEN"),
}


def get_base_url() -> str:
    """Get base URL based on environment."""
    env = settings["environment"].lower()
    env_urls = {
        "development": "http://localhost:3000",
        "staging": "https://api.staging.example.com",
        "production": "https://api.example.com",
    }
    return env_urls.get(env, settings["api_base_url"])


def get_headers() -> dict:
    """Get default headers."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "API-Tests/1.0",
    }

    if settings["auth_token"]:
        headers["Authorization"] = f"Bearer {settings['auth_token']}"

    return headers
