import logging

from fastmcp import FastMCP

from src.config import settings
from src.storage.chroma import ChromaStorage
from src.storage.sqlite import SQLiteStorage

logging.basicConfig(
    level=settings.LOG_LEVEL or "INFO",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

sql_storage = SQLiteStorage(db_path=settings.SQLITE_DB_PATH)
chroma_storage = ChromaStorage(db_path=settings.CHROMA_DB_PATH)

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


if __name__ == "__main__":
    mcp.run()
