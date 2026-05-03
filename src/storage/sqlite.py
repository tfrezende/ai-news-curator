import json
import sqlite3
from datetime import datetime

from src.models import Article


class SQLiteStorage:
    """
    SQLiteStorage is a simple storage backend for the AI News Curator application that uses SQLite to store news articles. It provides methods to insert articles, check for the existence of an article by ID, and retrieve recent articles from the database.

    Attributes:
        db_path (str): The file path to the SQLite database.
        conn (sqlite3.Connection): The SQLite connection object.

    Methods:
        insert_article(article: Article) -> None: Inserts a new article into the database.
        exists_article(article_id: str) -> bool: Checks if an article with the given ID exists in the database.
        get_recent_articles(limit: int = 10) -> list[Article]: Retrieves a list of recent articles from the database, ordered by publication date.
        close() -> None: Closes the database connection.
    """

    def __init__(self, db_path: str) -> None:
        """
        Initializes the SQLiteStorage instance by setting the database path and establishing a connection.
        Args:
            db_path (str): The file path to the SQLite database.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._initialize_db()

    def _initialize_db(self) -> None:
        """
        Initializes the SQLite database by creating the necessary tables if they do not exist.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                source TEXT NOT NULL,
                published_at TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                summary TEXT,
                raw_text TEXT,
                topics TEXT
            )
        """)
        self.conn.commit()

    def insert_article(self, article: Article) -> None:
        """
        Inserts a new article into the database.
        Args:
            article (Article): The Article object to be inserted into the database.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO articles (id, title, url, source, published_at, fetched_at, summary, raw_text, topics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                article.id,
                article.title,
                article.url,
                article.source,
                article.published_at.isoformat(),
                article.fetched_at.isoformat(),
                article.summary,
                article.raw_text,
                json.dumps(article.topics or []),
            ),
        )
        self.conn.commit()

    def exists_article(self, article_id: str) -> bool:
        """
        Checks if an article with the given ID exists in the database.
        Args:
            article_id (str): The ID of the article to check for existence.
        Returns:
            bool: True if the article exists in the database, False otherwise.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM articles WHERE id = ?
        """,
            (article_id,),
        )
        count = cursor.fetchone()[0]
        return count > 0

    def get_recent_articles(self, limit: int = 10) -> list[Article]:
        """
        Retrieves a list of recent articles from the database, ordered by publication date.
        Args:
            limit (int): The maximum number of recent articles to retrieve. Defaults to 10.
        Returns:
            list[Article]: A list of Article objects representing the recent articles.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, title, url, source, published_at, fetched_at, summary, raw_text, topics FROM articles
            ORDER BY published_at DESC
            LIMIT ?
        """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [
            Article(
                id=row["id"],
                title=row["title"],
                url=row["url"],
                source=row["source"],
                published_at=datetime.fromisoformat(row["published_at"]),
                fetched_at=datetime.fromisoformat(row["fetched_at"]),
                summary=row["summary"],
                raw_text=row["raw_text"],
                topics=json.loads(row["topics"]) if row["topics"] else [],
            )
            for row in rows
        ]

    def close(self) -> None:
        """
        Closes the database connection.
        """
        self.conn.close()
