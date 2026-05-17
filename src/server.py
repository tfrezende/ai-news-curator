import logging
import sys
from pathlib import Path

# Ensure the project root is on sys.path when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastmcp import FastMCP

from src.config import settings
from src.storage.chroma import ChromaStorage
from src.storage.sqlite import SQLiteStorage
from src.services.news_service import NewsService
from src.pipeline.ingest import IngestPipeline

logging.basicConfig(
    level=settings.LOG_LEVEL or "INFO",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

sql_storage = SQLiteStorage(db_path=settings.SQLITE_DB_PATH)
chroma_storage = ChromaStorage(db_path=settings.CHROMA_DB_PATH)
news_service = NewsService(sql_storage=sql_storage, chroma_storage=chroma_storage)
ingest_pipeline = IngestPipeline(sql_storage=sql_storage, chroma_storage=chroma_storage)

mcp = FastMCP("ai-news-curator")


@mcp.tool()
def health_check() -> dict:
    """
    A simple health check tool that returns a message indicating that the AI News Curator is running.
    Returns:
        dict: A dictionary containing the status of the AI News Curator and its storage components.
    """
    return {
        "status": "ok",
        "message": "AI News Curator is running!",
        "sqlite_status": "ok" if sql_storage else "error",
        "chroma_status": "ok" if chroma_storage else "error",
    }


@mcp.tool()
def search_news(query: str) -> list[dict]:
    """
    Search for news articles matching the given query.
    Args:
        query (str): The search query string.
    Returns:
        list[dict]: A list of dictionaries containing the search results.
    """
    return news_service.search_news(query)


@mcp.tool()
def get_article(article_id: int) -> dict:
    """
    Retrieve a news article by its ID.
    Args:
        article_id (int): The unique identifier of the article.
    Returns:
        dict: A dictionary containing the article details.
    """
    return news_service.get_article(article_id)


@mcp.tool()
def get_latest_articles() -> list[dict]:
    """
    Retrieve the latest news articles.
    Returns:
        list[dict]: A list of dictionaries containing the latest articles.
    """
    return news_service.get_latest_articles()


@mcp.tool()
def run_ingestion() -> None:
    """
    A placeholder tool for running the news ingestion process.
    This will be a scheduled job later.
    """
    logger.info("Running news ingestion pipeline...")
    ingest_pipeline.run()
    logger.info("News ingestion pipeline completed.")

if __name__ == "__main__":
    mcp.run()
