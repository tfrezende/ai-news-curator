import logging

from src.fetchers.content import fetch_article_content
from src.fetchers.hackernews import HackerNewsFetcher
from src.storage.chroma import ChromaStorage
from src.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


class IngestPipeline:
    """Pipeline to fetch articles from sources and store them in both SQLite and ChromaDB."""

    def __init__(self, sql_storage: SQLiteStorage, chroma_storage: ChromaStorage):
        self.sql_storage = sql_storage
        self.chroma_storage = chroma_storage
        self.fetchers = [HackerNewsFetcher()]

    def run(self) -> None:
        """Run the ingest pipeline: fetch articles and store them."""
        articles_stored = 0
        articles_skipped = 0
        articles_failed = 0
        for fetcher in self.fetchers:
            try:
                articles = fetcher.fetch()
                for article in articles:
                    if self.sql_storage.exists_article(article.id):
                        logger.info(
                            f"Article already exists in storage, skipping: {article.url}"
                        )
                        articles_skipped += 1
                    else:
                        logger.info(f"Ingesting new article: {article.url}")
                        article_content = fetch_article_content(article.url)
                        new_article = article.model_copy(
                            update={"raw_text": article_content}
                        )
                        try:
                            self.sql_storage.insert_article(new_article)
                            self.chroma_storage.insert_article(new_article)
                            articles_stored += 1
                        except Exception as e:
                            logger.error(
                                f"Error storing article {new_article.id} of {fetcher.source_name}: {e}"
                            )
                            articles_failed += 1
                            continue
            except Exception as e:
                logger.error(f"Error processing fetcher {fetcher.source_name}: {e}")
                continue
        logger.info(
            f"Articles stored: {articles_stored}, Articles skipped: {articles_skipped}, Articles failed: {articles_failed}"
        )
