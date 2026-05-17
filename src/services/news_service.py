from src.storage.chroma import ChromaStorage
from src.storage.sqlite import SQLiteStorage


class NewsService:
    """Service layer for handling news-related operations, interfacing with both SQLite and ChromaDB storages."""

    def __init__(
        self, sql_storage: SQLiteStorage, chroma_storage: ChromaStorage
    ) -> None:
        self.sql_storage = sql_storage
        self.chroma_storage = chroma_storage

    def search_news(self, query: str, limit: int = 10) -> list[dict]:
        """Search for news articles matching the query."""
        return self.chroma_storage.search_articles(query, n_results=limit)

    def get_article(self, article_id: int) -> dict:
        """Retrieve a news article by its ID."""
        return self.sql_storage.get_article_by_id(article_id)

    def get_latest_articles(self, limit: int = 10) -> list[dict]:
        """Retrieve the latest news articles."""
        return self.sql_storage.get_recent_articles(limit=limit)
