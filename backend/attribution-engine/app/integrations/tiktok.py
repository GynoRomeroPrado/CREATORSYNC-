"""
TikTok API integration.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.integrations.base import PlatformIntegration
from app.core.config import settings


class TikTokIntegration(PlatformIntegration):
    """
    TikTok for Developers API integration.

    Uses TikTok's Display API and Creator API.
    """

    BASE_URL = "https://open.tiktokapis.com/v2"

    def get_rate_limit(self) -> int:
        """TikTok: 1000 requests per day."""
        return settings.RATE_LIMIT_TIKTOK

    async def get_content(
        self,
        user_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch videos from TikTok.

        Note: Requires proper OAuth token with video.list permission.

        Args:
            user_id: TikTok user ID
            date_from: Start date
            date_to: End date

        Returns:
            List of video data
        """
        await self.rate_limiter.acquire()

        if not self.access_token:
            raise ValueError("Access token required for TikTok API")

        videos = []
        cursor = 0
        has_more = True

        while has_more:
            await self.rate_limiter.acquire()

            response = await self.client.post(
                f"{self.BASE_URL}/video/list/",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "max_count": 20,
                    "cursor": cursor
                }
            )

            data = response.json()

            if data.get("error"):
                break

            for video in data.get("data", {}).get("videos", []):
                created_time = datetime.fromtimestamp(video.get("create_time", 0))

                # Filter by date
                if date_from and created_time < date_from:
                    continue
                if date_to and created_time > date_to:
                    continue

                videos.append({
                    "platform_content_id": video.get("id"),
                    "content_type": "short",  # TikTok is all short-form
                    "title": video.get("title", "")[:100],
                    "description": video.get("description", ""),
                    "url": video.get("share_url", ""),
                    "thumbnail_url": video.get("cover_image_url", ""),
                    "published_at": created_time,
                    "views": video.get("view_count", 0),
                    "likes": video.get("like_count", 0),
                    "comments": video.get("comment_count", 0),
                    "shares": video.get("share_count", 0),
                    "metadata": {
                        "duration": video.get("duration", 0),
                        "hashtags": video.get("hashtags", [])
                    }
                })

            has_more = data.get("data", {}).get("has_more", False)
            cursor = data.get("data", {}).get("cursor", 0)

        return videos

    async def get_analytics(self, content_id: str) -> Dict[str, Any]:
        """
        Get analytics for a specific TikTok video.

        Args:
            content_id: TikTok video ID

        Returns:
            Analytics data
        """
        await self.rate_limiter.acquire()

        if not self.access_token:
            raise ValueError("Access token required")

        response = await self.client.post(
            f"{self.BASE_URL}/video/query/",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            json={
                "filters": {
                    "video_ids": [content_id]
                }
            }
        )

        data = response.json()
        videos = data.get("data", {}).get("videos", [])

        if not videos:
            return {}

        video = videos[0]
        views = video.get("view_count", 0)
        likes = video.get("like_count", 0)
        comments = video.get("comment_count", 0)
        shares = video.get("share_count", 0)

        # Calculate engagement rate
        if views > 0:
            engagement_rate = ((likes + comments + shares) / views) * 100
        else:
            engagement_rate = 0.0

        return {
            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "engagement_rate": round(engagement_rate, 2)
        }

    async def get_income(
        self,
        user_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch income data from TikTok Creator Fund.

        Note: TikTok doesn't provide direct API access to Creator Fund earnings.
        This would need to be manually entered or scraped from Creator Portal.

        Args:
            user_id: TikTok user ID
            date_from: Start date
            date_to: End date

        Returns:
            List of income records
        """
        # TikTok doesn't expose Creator Fund earnings via API
        # Users would need to manually enter or integrate via web scraping
        return []
