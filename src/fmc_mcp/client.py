"""FMC API Client with authentication, rate limiting, and pagination."""

import asyncio
import base64
import logging
import time
from typing import Any

import httpx

from fmc_mcp.config import FMCSettings, get_settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for FMC API requests."""

    def __init__(self, capacity: int = 120, refill_rate: float = 2.0) -> None:
        """Initialize rate limiter.

        Args:
            capacity: Maximum tokens (requests) in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            await self._refill()

            while self.tokens < 1:
                wait_time = (1 - self.tokens) / self.refill_rate
                logger.warning(
                    "Rate limit approaching: %.1f tokens remaining, waiting %.2fs",
                    self.tokens,
                    wait_time,
                )
                await asyncio.sleep(wait_time)
                await self._refill()

            self.tokens -= 1

            # Log warning when bucket is running low
            if self.tokens < self.capacity * 0.2:
                logger.warning(
                    "Rate limit bucket low: %.1f/%d tokens remaining",
                    self.tokens,
                    self.capacity,
                )

    async def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now


class FMCClient:
    """Async client for Cisco FMC REST API."""

    def __init__(self, settings: FMCSettings | None = None) -> None:
        """Initialize FMC client.

        Args:
            settings: FMC connection settings (uses env if not provided)
        """
        self.settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._domain_uuid: str | None = self.settings.fmc_domain_uuid
        self._refresh_count: int = 0
        self._max_refreshes: int = 3
        self._rate_limiter = RateLimiter(
            capacity=self.settings.fmc_rate_limit,
            refill_rate=self.settings.fmc_rate_limit / 60,
        )
        self._connection_semaphore = asyncio.Semaphore(self.settings.fmc_max_connections)

    @property
    def base_url(self) -> str:
        """Get FMC base URL."""
        return f"https://{self.settings.fmc_host}"

    @property
    def domain_uuid(self) -> str:
        """Get domain UUID, falling back to global default."""
        return self._domain_uuid or "e276abec-e0f2-11e3-8169-6d9ed49b625f"

    async def __aenter__(self) -> "FMCClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Initialize HTTP client and authenticate."""
        if self._client is not None:
            return

        self.settings.log_config()

        limits = httpx.Limits(
            max_keepalive_connections=5,
            max_connections=self.settings.fmc_max_connections,
        )

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            verify=self.settings.fmc_verify_ssl,
            limits=limits,
            timeout=httpx.Timeout(self.settings.fmc_timeout),
        )

        await self._authenticate()

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self._access_token = None
            self._refresh_token = None
            logger.info("FMC client connection closed")

    async def _authenticate(self) -> None:
        """Authenticate with FMC using Basic Auth."""
        if self._client is None:
            raise RuntimeError("Client not initialized. Call connect() first.")

        credentials = f"{self.settings.fmc_username}:{self.settings.fmc_password.get_secret_value()}"
        encoded = base64.b64encode(credentials.encode()).decode()

        logger.info("Authenticating with FMC at %s", self.settings.fmc_host)

        response = await self._client.post(
            "/api/fmc_platform/v1/auth/generatetoken",
            headers={"Authorization": f"Basic {encoded}"},
        )

        if response.status_code != 204:
            logger.error("Authentication failed: %d %s", response.status_code, response.text)
            raise RuntimeError(f"FMC authentication failed: {response.status_code}")

        self._access_token = response.headers.get("X-auth-access-token")
        self._refresh_token = response.headers.get("X-auth-refresh-token")
        self._refresh_count = 0

        # Extract domain UUID from response if not configured
        if not self._domain_uuid:
            domain_uuid = response.headers.get("DOMAIN_UUID")
            if domain_uuid:
                self._domain_uuid = domain_uuid
                logger.info("Discovered domain UUID: %s", self._domain_uuid)

        logger.info("Successfully authenticated with FMC")

    async def _refresh_auth_token(self) -> bool:
        """Refresh the access token.

        Returns:
            True if refresh succeeded, False if re-auth required
        """
        if self._client is None or not self._refresh_token:
            return False

        if self._refresh_count >= self._max_refreshes:
            logger.warning(
                "Reached max token refreshes (%d), performing full re-authentication",
                self._max_refreshes,
            )
            await self._authenticate()
            return True

        logger.info("Refreshing access token (refresh %d/%d)", self._refresh_count + 1, self._max_refreshes)

        try:
            headers: dict[str, str] = {}
            if self._access_token:
                headers["X-auth-access-token"] = self._access_token
            if self._refresh_token:
                headers["X-auth-refresh-token"] = self._refresh_token

            response = await self._client.post(
                "/api/fmc_platform/v1/auth/refreshtoken",
                headers=headers,
            )

            if response.status_code == 204:
                self._access_token = response.headers.get("X-auth-access-token")
                self._refresh_token = response.headers.get("X-auth-refresh-token")
                self._refresh_count += 1
                logger.info("Token refreshed successfully")
                return True

            logger.warning("Token refresh failed: %d, will re-authenticate", response.status_code)
            await self._authenticate()
            return True

        except Exception as e:
            logger.error("Token refresh error: %s, will re-authenticate", e)
            await self._authenticate()
            return True

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an authenticated request with rate limiting.

        Args:
            method: HTTP method
            path: API path
            **kwargs: Additional arguments for httpx

        Returns:
            HTTP response
        """
        if self._client is None:
            raise RuntimeError("Client not initialized. Call connect() first.")

        # Apply rate limiting
        await self._rate_limiter.acquire()

        # Apply connection limiting
        async with self._connection_semaphore:
            headers = kwargs.pop("headers", {})
            headers["X-auth-access-token"] = self._access_token

            response = await self._client.request(method, path, headers=headers, **kwargs)

            # Handle token expiration
            if response.status_code == 401:
                logger.info("Received 401, attempting token refresh")
                await self._refresh_auth_token()
                headers["X-auth-access-token"] = self._access_token
                response = await self._client.request(method, path, headers=headers, **kwargs)

            # Handle rate limiting
            if response.status_code == 429:
                logger.error("Rate limited by FMC (429 Too Many Requests)")
                retry_after = int(response.headers.get("Retry-After", "60"))
                logger.warning("Rate limited, waiting %d seconds", retry_after)
                await asyncio.sleep(retry_after)
                response = await self._client.request(method, path, headers=headers, **kwargs)

            return response

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make a GET request."""
        return await self._request("GET", path, **kwargs)

    async def get_json(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make a GET request and return JSON response."""
        response = await self.get(path, **kwargs)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    async def get_all_items(self, endpoint: str, expanded: bool = True) -> list[dict[str, Any]]:
        """Fetch all items from a paginated endpoint.

        Args:
            endpoint: API endpoint path
            expanded: Whether to request expanded item details

        Returns:
            List of all items from all pages
        """
        all_items: list[dict[str, Any]] = []
        limit = 1000
        offset = 0

        while True:
            params: dict[str, Any] = {"limit": limit, "offset": offset}
            if expanded:
                params["expanded"] = "true"

            logger.debug("Fetching %s with offset=%d, limit=%d", endpoint, offset, limit)

            response = await self.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            if not items:
                break

            all_items.extend(items)

            # Check if we've fetched all items
            paging = data.get("paging", {})
            total_count = paging.get("count", 0)

            logger.info(
                "Fetched %d items (total: %d/%d)",
                len(items),
                len(all_items),
                total_count,
            )

            if offset + limit >= total_count:
                break

            offset += limit

        return all_items

    # Convenience methods for common API calls

    async def get_server_version(self) -> dict[str, Any]:
        """Get FMC server version information."""
        return await self.get_json("/api/fmc_platform/v1/info/serverversion")

    async def get_domain_info(self) -> dict[str, Any]:
        """Get domain information."""
        return await self.get_json("/api/fmc_platform/v1/info/domain")

    async def get_devices(self) -> list[dict[str, Any]]:
        """Get all device records."""
        endpoint = f"/api/fmc_config/v1/domain/{self.domain_uuid}/devices/devicerecords"
        return await self.get_all_items(endpoint)

    async def get_network_objects(self) -> list[dict[str, Any]]:
        """Get all network objects."""
        endpoint = f"/api/fmc_config/v1/domain/{self.domain_uuid}/object/networks"
        return await self.get_all_items(endpoint)

    async def get_host_objects(self) -> list[dict[str, Any]]:
        """Get all host objects."""
        endpoint = f"/api/fmc_config/v1/domain/{self.domain_uuid}/object/hosts"
        return await self.get_all_items(endpoint)

    async def get_deployable_devices(self) -> list[dict[str, Any]]:
        """Get devices with pending deployments.

        Note: This endpoint may require elevated permissions and could return
        403 Forbidden on sandboxes or restricted accounts.
        """
        endpoint = f"/api/fmc_config/v1/domain/{self.domain_uuid}/deployment/deployabledevices"
        try:
            return await self.get_all_items(endpoint, expanded=True)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.warning(
                    "Deployment endpoint requires elevated permissions (403 Forbidden)"
                )
                return []
            raise

    async def test_connection(self) -> None:
        """Test connection to FMC and print version info."""
        async with self:
            version = await self.get_server_version()
            print(f"Connected to FMC: {self.settings.fmc_host}")  # noqa: T201
            print(f"Server Version: {version.get('serverVersion', 'Unknown')}")  # noqa: T201
            print("Authentication: Success")  # noqa: T201
