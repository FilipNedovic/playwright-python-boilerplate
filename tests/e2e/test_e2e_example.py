import json

import allure
import pytest
import structlog

logger = structlog.get_logger(__name__)


@allure.epic("E2E Tests")
@pytest.mark.e2e
class TestE2E:

    @allure.title("Basic Click Interaction Test")
    @pytest.mark.smoke
    def test_basic_click_interaction(self, page):
        """Classic E2E: render a small page and verify a button click updates UI."""
        page.set_content(
            """
            <html>
                <body>
                    <div id="status">not clicked</div>
                    <button id="btn">Click me</button>
                    <script>
                        document.getElementById('btn').addEventListener('click', function() {
                            document.getElementById('status').textContent = 'clicked';
                        });
                    </script>
                </body>
            </html>
            """
        )

        btn = page.locator("#btn")
        status = page.locator("#status")

        # verify initial state
        assert status.text_content().strip() == "not clicked"

        # perform click and verify state change
        btn.click()
        assert status.text_content().strip() == "clicked"
        logger.info("✅ Clicked button and verified UI update")

    @allure.title("Test Intercept with Page Fixture")
    @pytest.mark.smoke
    def test_intercept_using_page(self, page):
        """Verify interception using the pytest-playwright `page` fixture (sync)."""
        expected = {"id": 1, "title": "stubbed"}

        def handler(route):
            try:
                route.fulfill(
                    status=200,
                    headers={"Content-Type": "application/json"},
                    body=json.dumps(expected),
                )
            except Exception as e:
                raise e

        page.route("**/posts/1", handler)

        url = "https://jsonplaceholder.typicode.com/posts/1"
        data = page.evaluate("(url) => fetch(url).then(r => r.json())", url)

        assert data["id"] == expected["id"]
        assert data["title"] == expected["title"]

        logger.info("✅ Intercepted request and returned stubbed response")
        page.unroute("**/posts/1", handler)
