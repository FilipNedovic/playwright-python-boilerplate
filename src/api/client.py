import time
from typing import Any, Dict, List, Optional, Union

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class APIClient:
    """Async API client using httpx.AsyncClient.

    Methods mirror the previous sync client but are async. Tests/fixtures should
    `await` the calls (pytest asyncio mode is enabled).
    """

    def __init__(self, base_url: str = "", default_headers: Optional[Dict] = None):
        self.base_url = base_url.rstrip("/") if base_url else ""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "API-Test-Client/1.0",
        }
        if default_headers:
            headers.update(default_headers)

        self.client = httpx.AsyncClient(headers=headers)

    async def set_auth_token(self, token: str):
        """Set authentication token on client headers."""
        self.client.headers["Authorization"] = f"Bearer {token}"

    def set_base_url(self, base_url: str):
        """Update base URL."""
        self.base_url = base_url.rstrip("/")

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith(("http://", "https://")):
            return endpoint
        if self.base_url:
            return f"{self.base_url}/{endpoint.lstrip('/')}"
        return endpoint

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.ReadTimeout)),
    )
    async def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Union[Dict, List, str]] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: float = 30.0,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make HTTP request asynchronously."""
        url = self._build_url(endpoint)

        request_kwargs = {
            "params": params,
            "timeout": timeout,
            **kwargs,
        }

        if headers:
            request_kwargs["headers"] = headers

        if data is not None:
            if isinstance(data, (dict, list)):
                request_kwargs["json"] = data
            else:
                request_kwargs["content"] = str(data)

        logger.debug("Making request", method=method, url=url, timeout=timeout)

        start_time = time.time()

        try:
            response = await self.client.request(method=method.upper(), url=url, **request_kwargs)

            elapsed = time.time() - start_time

            # Try to parse JSON
            response_data = None
            try:
                ct = response.headers.get("content-type", "")
                if ct.startswith("application/json"):
                    response_data = response.json()
                else:
                    response_data = response.text
            except Exception:
                response_data = response.text

            logger.debug(
                "Received response",
                method=method,
                url=url,
                status=response.status_code,
                response_time=f"{elapsed:.3f}s",
            )

            return {
                "status": response.status_code,
                "ok": response.is_success,
                "headers": dict(response.headers),
                "data": response_data,
                "text": response.text,
                "elapsed": elapsed,
                "response": response,
            }

        except Exception as e:
            logger.error("Request failed", url=url, method=method, error=str(e))
            raise

    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return await self.request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, data: Optional[Union[Dict, List, str]] = None, **kwargs) -> Dict[str, Any]:
        return await self.request("POST", endpoint, data=data, **kwargs)

    async def put(self, endpoint: str, data: Optional[Union[Dict, List, str]] = None, **kwargs) -> Dict[str, Any]:
        return await self.request("PUT", endpoint, data=data, **kwargs)

    async def patch(self, endpoint: str, data: Optional[Union[Dict, List, str]] = None, **kwargs) -> Dict[str, Any]:
        return await self.request("PATCH", endpoint, data=data, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return await self.request("DELETE", endpoint, **kwargs)

    async def health_check(self) -> bool:
        try:
            result = await self.get("health", timeout=5.0)
            return result["status"] == 200
        except Exception:
            return False

    async def close(self):
        await self.client.aclose()
