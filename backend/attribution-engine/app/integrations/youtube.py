"""
YouTube Data API integration.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.integrations.base import PlatformIntegration
from app.core.config import settings


class YouTubeIntegration(PlatformIntegration):
    """YouTube Data API v3 integration."""

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def get_rate_limit(self) -> int:
        """YouTube: 10,000 quota units per day."""
        return settings.RATE_LIMIT_YOUTUBE

    async def get_content(
        self,
        user_id: str,  # Channel ID
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch videos from a YouTube channel.

        Args:
            user_id: YouTube channel ID
            date_from: Start date for filtering
            date_to: End date for filtering

        Returns:
            List of video data dictionaries
        """
        await self.rate_limiter.acquire()

        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=365)

        # First, get the uploads playlist ID
        channel_response = await self.client.get(
            f"{self.BASE_URL}/channels",
            params={
                "part": "contentDetails",
                "id": user_id,
                "key": settings.YOUTUBE_API_KEY
            }
        )
        channel_data = channel_response.json()

        if not channel_data.get("items"):
            return []

        uploads_playlist_id = channel_data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        # Get videos from uploads playlist
        videos = []
        next_page_token = None

        while True:
            await self.rate_limiter.acquire()

            params = {
                "part": "snippet,contentDetails",
                "playlistId": uploads_playlist_id,
                "maxResults": 50,
                "key": settings.YOUTUBE_API_KEY
            }

            if next_page_token:
                params["pageToken"] = next_page_token

            response = await self.client.get(
                f"{self.BASE_URL}/playlistItems",
                params=params
            )
            data = response.json()

            for item in data.get("items", []):
                video_id = item["contentDetails"]["videoId"]
                snippet = item["snippet"]

                published_at = datetime.fromisoformat(
                    snippet["publishedAt"].replace("Z", "+00:00")
                )

                # Filter by date
                if date_from and published_at < date_from:
                    continue
                if date_to and published_at > date_to:
                    continue

                # Get detailed statistics for each video
                video_stats = await self.get_analytics(video_id)

                videos.append({
                    "platform_content_id": video_id,
                    "content_type": "video",
                    "title": snippet["title"],
                    "description": snippet["description"],
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "thumbnail_url": snippet["thumbnails"]["high"]["url"],
                    "published_at": published_at,
                    "views": video_stats.get("views", 0),
                    "likes": video_stats.get("likes", 0),
                    "comments": video_stats.get("comments", 0),
                    "metadata": {
                        "tags": snippet.get("tags", []),
                        "category_id": snippet.get("categoryId")
                    }
                })

            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break

        return videos

    async def get_analytics(self, content_id: str) -> Dict[str, Any]:
        """
        Get detailed analytics for a specific video.

        Args:
            content_id: YouTube video ID

        Returns:
            Dictionary with analytics data
        """
        await self.rate_limiter.acquire()

        response = await self.client.get(
            f"{self.BASE_URL}/videos",
            params={
                "part": "statistics,contentDetails",
                "id": content_id,
                "key": settings.YOUTUBE_API_KEY
            }
        )
        data = response.json()

        if not data.get("items"):
            return {}

        stats = data["items"][0]["statistics"]
        content_details = data["items"][0]["contentDetails"]

        # Parse duration (PT1H2M3S format)
        duration_str = content_details.get("duration", "PT0S")
        duration_minutes = self._parse_duration(duration_str)

        return {
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "watch_time_minutes": duration_minutes * int(stats.get("viewCount", 0)),
            "engagement_rate": self._calculate_engagement(stats)
        }

    async def get_income(
        self,
        user_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch income data from YouTube.

        Note: This requires YouTube Analytics API and channel ownership.
        For now, returns empty list as it requires OAuth and special permissions.

        Args:
            user_id: YouTube channel ID
            date_from: Start date
            date_to: End date

        Returns:
            List of income records
        """
        # YouTube Analytics API requires OAuth and channel ownership
        # This would be implemented with proper OAuth flow
        # For MVP, income would be manually entered
        return []

    @staticmethod
    def _parse_duration(duration: str) -> int:
        """Parse ISO 8601 duration to minutes."""
        import re

        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration)

        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 60 + minutes + seconds // 60

    @staticmethod
    def _calculate_engagement(stats: dict) -> float:
        """Calculate engagement rate."""
        views = int(stats.get("viewCount", 0))
        if views == 0:
            return 0.0

        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))

        engagement = (likes + comments) / views
        return round(engagement * 100, 2)  # Percentage
