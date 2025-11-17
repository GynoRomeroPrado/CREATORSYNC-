"""
Base class for platform integrations.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
import asyncio
from app.core.config import settings


class PlatformIntegration(ABC):
    """Abstract base class for platform integrations."""

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.client = httpx.AsyncClient(timeout=30.0)
        self.rate_limiter = RateLimiter(self.get_rate_limit())

    @abstractmethod
    def get_rate_limit(self) -> int:
        """Get rate limit for this platform."""
        pass

    @abstractmethod
    async def get_content(
        self,
        user_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Fetch content from the platform."""
        pass

    @abstractmethod
    async def get_income(
        self,
        user_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Fetch income data from the platform."""
        pass

    @abstractmethod
    async def get_analytics(
        self,
        content_id: str
    ) -> Dict[str, Any]:
        """Get analytics for specific content."""
        pass

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, max_calls_per_period: int, period_seconds: int = 60):
        self.max_calls = max_calls_per_period
        self.period = period_seconds
        self.calls = []

    async def acquire(self):
        """Wait if necessary to respect rate limits."""
        now = datetime.utcnow().timestamp()

        # Remove old calls outside the period
        self.calls = [call for call in self.calls if call > now - self.period]

        # If at limit, wait
        if len(self.calls) >= self.max_calls:
            sleep_time = self.calls[0] + self.period - now
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            self.calls = []

        self.calls.append(now)
