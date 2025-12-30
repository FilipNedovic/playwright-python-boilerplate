import allure
import pytest
import structlog

logger = structlog.get_logger(__name__)


@allure.epic("API Tests")
@pytest.mark.api
class TestAPI:

    @allure.title("Test Google Homepage")
    @pytest.mark.smoke
    async def test_google_accessible(self, api_client):
        """Test Google API."""
        logger.info("Testing access to Google homepage")
        result = await api_client.get("https://www.google.com", timeout=5)

        assert result["status"] == 200
        assert "Google" in result["text"]
        logger.info(f"✅ Completed in {result['elapsed']:.2f}s")

    @allure.title("Test JSON API")
    @pytest.mark.smoke
    async def test_json_api(self, api_client):
        """Test JSONPlaceholder API."""
        result = await api_client.get("https://jsonplaceholder.typicode.com/posts/1")

        assert result["status"] == 200
        data = result["data"]
        assert data["id"] == 1
        assert "title" in data

        logger.info(f"Completed in {result['elapsed']:.2f}s")
