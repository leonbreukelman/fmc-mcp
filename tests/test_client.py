"""Tests for FMC client."""

import asyncio
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import AsyncMock

import pytest
from pytest_httpx import HTTPXMock

from fmc_mcp.client import FMCClient, RateLimiter
from fmc_mcp.config import FMCSettings


class CountingLimiter(RateLimiter):
    """Minimal rate-limiter spy."""

    def __init__(self) -> None:
        self.count = 0

    async def acquire(self) -> None:
        """Record an attempted HTTP request."""
        self.count += 1


class TestRateLimiter:
    """Tests for the RateLimiter class."""

    @pytest.mark.asyncio
    async def test_acquire_token(self) -> None:
        """Test acquiring a single token."""
        limiter = RateLimiter(capacity=10, refill_rate=1.0)
        await limiter.acquire()
        assert limiter.tokens < 10

    @pytest.mark.asyncio
    async def test_multiple_acquires(self) -> None:
        """Test acquiring multiple tokens."""
        limiter = RateLimiter(capacity=5, refill_rate=1.0)
        for _ in range(3):
            await limiter.acquire()
        assert limiter.tokens < 3

    @pytest.mark.parametrize(
        ("capacity", "refill_rate"),
        [(0, 1.0), (-1, 1.0), (1, 0.0), (1, -1.0)],
    )
    def test_rejects_non_positive_limits(self, capacity: int, refill_rate: float) -> None:
        """A limiter must never accept values that can deadlock or divide by zero."""
        with pytest.raises(ValueError, match="positive"):
            RateLimiter(capacity=capacity, refill_rate=refill_rate)


class TestFMCClient:
    """Tests for the FMCClient class."""

    def test_base_url(self, fmc_settings: FMCSettings) -> None:
        """Test base URL construction."""
        client = FMCClient(fmc_settings)
        assert client.base_url == "https://fmc.test.local"

    def test_domain_uuid_from_settings(self, fmc_settings: FMCSettings) -> None:
        """Test domain UUID from settings."""
        client = FMCClient(fmc_settings)
        assert client.domain_uuid == "test-domain-uuid"

    def test_domain_uuid_default(self) -> None:
        """Test default domain UUID fallback."""
        settings = FMCSettings(
            fmc_host="fmc.test.local",
            fmc_username="test",
            fmc_password="test",  # type: ignore[arg-type]
        )
        client = FMCClient(settings)
        # Should return global default
        assert client.domain_uuid == "e276abec-e0f2-11e3-8169-6d9ed49b625f"

    @pytest.mark.asyncio
    async def test_authentication(
        self,
        fmc_client: FMCClient,
        mock_auth_response: None,
    ) -> None:
        """Test successful authentication."""
        await fmc_client.connect()
        assert fmc_client._access_token == "test-access-token"
        assert fmc_client._refresh_token == "test-refresh-token"
        await fmc_client.close()

    @pytest.mark.asyncio
    async def test_authentication_consumes_rate_limit_capacity(
        self,
        fmc_client: FMCClient,
        mock_auth_response: None,
    ) -> None:
        """Authentication is an FMC API request and must be rate limited."""
        limiter = CountingLimiter()
        fmc_client._rate_limiter = limiter

        await fmc_client.connect()

        assert limiter.count == 1
        await fmc_client.close()

    @pytest.mark.asyncio
    async def test_authentication_rejects_missing_access_token(
        self,
        fmc_client: FMCClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """A nominal 204 response without an access token is not authenticated."""
        httpx_mock.add_response(
            method="POST",
            url="https://fmc.test.local/api/fmc_platform/v1/auth/generatetoken",
            status_code=204,
            headers={"X-auth-refresh-token": "refresh-token"},
        )

        with pytest.raises(RuntimeError, match="access token"):
            await fmc_client.connect()
        await fmc_client.close()

    @pytest.mark.asyncio
    async def test_get_server_version(
        self,
        fmc_client: FMCClient,
        mock_auth_response: None,
        mock_server_version: None,
    ) -> None:
        """Test fetching server version."""
        async with fmc_client:
            version = await fmc_client.get_server_version()
            assert version["serverVersion"] == "7.4.2.3"

    @pytest.mark.asyncio
    async def test_get_devices(
        self,
        fmc_client: FMCClient,
        mock_auth_response: None,
        mock_devices: None,
    ) -> None:
        """Test fetching device records."""
        async with fmc_client:
            devices = await fmc_client.get_devices()
            assert len(devices) == 2
            assert devices[0]["name"] == "FTD-01"
            assert devices[1]["name"] == "FTD-02"

    @pytest.mark.asyncio
    async def test_get_network_objects(
        self,
        fmc_client: FMCClient,
        mock_auth_response: None,
        mock_network_objects: None,
    ) -> None:
        """Test fetching network objects."""
        async with fmc_client:
            objects = await fmc_client.get_network_objects()
            assert len(objects) == 2
            assert objects[0]["name"] == "Internal-Network"

    @pytest.mark.asyncio
    async def test_token_refresh_on_401(
        self,
        fmc_client: FMCClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Test automatic token refresh on 401 response."""
        # Initial auth
        httpx_mock.add_response(
            method="POST",
            url="https://fmc.test.local/api/fmc_platform/v1/auth/generatetoken",
            status_code=204,
            headers={
                "X-auth-access-token": "old-token",
                "X-auth-refresh-token": "refresh-token",
            },
        )

        # First request returns 401
        httpx_mock.add_response(
            method="GET",
            url="https://fmc.test.local/api/fmc_platform/v1/info/serverversion",
            status_code=401,
        )

        # Token refresh
        httpx_mock.add_response(
            method="POST",
            url="https://fmc.test.local/api/fmc_platform/v1/auth/refreshtoken",
            status_code=204,
            headers={
                "X-auth-access-token": "new-token",
                "X-auth-refresh-token": "new-refresh-token",
            },
        )

        # Retry with new token succeeds
        httpx_mock.add_response(
            method="GET",
            url="https://fmc.test.local/api/fmc_platform/v1/info/serverversion",
            json={"serverVersion": "7.4.2.3"},
        )

        async with fmc_client:
            version = await fmc_client.get_server_version()
            assert version["serverVersion"] == "7.4.2.3"
            assert fmc_client._access_token == "new-token"
            assert fmc_client._refresh_count == 1

    @pytest.mark.asyncio
    async def test_refresh_rejects_missing_access_token(
        self,
        fmc_client: FMCClient,
        mock_auth_response: None,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Refresh must not replace a valid token with a missing header."""
        await fmc_client.connect()
        httpx_mock.add_response(
            method="POST",
            url="https://fmc.test.local/api/fmc_platform/v1/auth/refreshtoken",
            status_code=204,
            headers={"X-auth-refresh-token": "new-refresh-token"},
        )

        with pytest.raises(RuntimeError, match="access token"):
            await fmc_client._refresh_auth_token()
        await fmc_client.close()

    @pytest.mark.asyncio
    async def test_concurrent_refreshes_are_coalesced(
        self,
        fmc_client: FMCClient,
        mock_auth_response: None,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Concurrent 401 handlers must perform one refresh for the stale token."""
        await fmc_client.connect()
        httpx_mock.add_response(
            method="POST",
            url="https://fmc.test.local/api/fmc_platform/v1/auth/refreshtoken",
            status_code=204,
            headers={
                "X-auth-access-token": "new-token",
                "X-auth-refresh-token": "new-refresh-token",
            },
        )

        results = await asyncio.gather(
            fmc_client._refresh_auth_token("test-access-token"),
            fmc_client._refresh_auth_token("test-access-token"),
        )

        assert len(results) == 2
        assert all(results)
        assert fmc_client._refresh_count == 1
        await fmc_client.close()

    @pytest.mark.asyncio
    async def test_retry_attempt_is_rate_limited_and_accepts_http_date(
        self,
        fmc_client: FMCClient,
        mock_auth_response: None,
        httpx_mock: HTTPXMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Every 429 retry is counted and RFC date-form Retry-After is supported."""
        await fmc_client.connect()
        limiter = CountingLimiter()
        fmc_client._rate_limiter = limiter
        retry_at = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=5), usegmt=True)
        httpx_mock.add_response(
            method="GET",
            url="https://fmc.test.local/api/fmc_platform/v1/info/serverversion",
            status_code=429,
            headers={"Retry-After": retry_at},
        )
        httpx_mock.add_response(
            method="GET",
            url="https://fmc.test.local/api/fmc_platform/v1/info/serverversion",
            json={"serverVersion": "7.4.2.3"},
        )
        sleep = AsyncMock()
        monkeypatch.setattr(asyncio, "sleep", sleep)

        version = await fmc_client.get_server_version()

        assert version["serverVersion"] == "7.4.2.3"
        assert limiter.count == 2
        sleep.assert_awaited_once()
        assert sleep.await_args is not None
        assert 0 <= sleep.await_args.args[0] <= 5
        await fmc_client.close()

    @pytest.mark.asyncio
    async def test_pagination_continues_without_reliable_count(
        self,
        fmc_client: FMCClient,
        mock_auth_response: None,
        httpx_mock: HTTPXMock,
    ) -> None:
        """A full page must not be treated as final when paging.count is absent."""
        await fmc_client.connect()
        first_page = [{"id": f"item-{index}"} for index in range(1000)]
        httpx_mock.add_response(
            method="GET",
            url="https://fmc.test.local/items?limit=1000&offset=0&expanded=true",
            json={"items": first_page, "paging": {"next": "/items?offset=1000"}},
        )
        httpx_mock.add_response(
            method="GET",
            url="https://fmc.test.local/items?limit=1000&offset=1000&expanded=true",
            json={"items": [{"id": "item-1000"}], "paging": {}},
        )

        items = await fmc_client.get_all_items("/items")

        assert len(items) == 1001
        assert items[-1]["id"] == "item-1000"
        await fmc_client.close()

    @pytest.mark.asyncio
    async def test_context_manager(
        self,
        fmc_client: FMCClient,
        mock_auth_response: None,
    ) -> None:
        """Test async context manager."""
        async with fmc_client:
            assert fmc_client._client is not None
        assert fmc_client._client is None
