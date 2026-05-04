import logging
from datetime import datetime

import httpx

from src.fetchers.base import BaseFetcher
from src.models import Article

logger = logging.getLogger(__name__)


class HackerNewsFetcher(BaseFetcher):
    """Fetcher for Hacker News articles using the official API."""

    @property
    def source_name(self) -> str:
        return "Hacker News"

    def fetch(self, limit: int = 30) -> list[Article]:
        """
        Fetches the top articles from Hacker News.

        Args:
            limit (int): The maximum number of articles to fetch.

        Returns:
            list[Article]: A list of Article objects.
        """
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        response = httpx.get(url)
        response.raise_for_status()
        story_ids = response.json()[:limit]

        articles = []
        for story_id in story_ids:
            try:
                story_url = (
                    f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                )
                story_response = httpx.get(story_url)
                story_response.raise_for_status()
                story_data = story_response.json()

                if self._is_valid_story(story_data):
                    article = Article(
                        title=story_data.get("title"),
                        url=story_data.get("url"),
                        source=self.source_name,
                        published_at=datetime.fromtimestamp(story_data.get("time")),
                    )
                    articles.append(article)
            except httpx.HTTPError as e:
                logger.warning(f"Error fetching story {story_id}: {e}")
                continue
        return articles

    def _is_valid_story(self, story_data: dict) -> bool:
        """Check if the story data contains the required fields."""
        return (
            story_data
            and "title" in story_data
            and "url" in story_data
            and story_data.get("time") is not None
        )
