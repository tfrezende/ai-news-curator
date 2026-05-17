"""Unit tests for SQLiteStorage (src/storage/sqlite.py)."""

from datetime import datetime

import pytest

from src.models import Article
from src.storage.sqlite import SQLiteStorage


@pytest.fixture
def storage():
    """Return an in-memory SQLiteStorage instance, closed after each test."""
    store = SQLiteStorage(db_path=":memory:")
    yield store
    store.close()


def _make_article(**overrides) -> Article:
    defaults = dict(
        title="Default Title",
        url="https://example.com/article/1",
        source="Example News",
        published_at=datetime(2024, 3, 10, 9, 0, 0),
    )
    defaults.update(overrides)
    return Article(**defaults)


class TestSQLiteStorageInit:
    def test_creates_articles_table(self, storage):
        cursor = storage.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='articles'"
        )
        result = cursor.fetchone()
        assert result is not None

    def test_table_is_empty_initially(self, storage):
        cursor = storage.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        assert cursor.fetchone()[0] == 0


class TestInsertArticle:
    def test_insert_article_adds_row(self, storage):
        article = _make_article()
        storage.insert_article(article)

        cursor = storage.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles WHERE id = ?", (article.id,))
        assert cursor.fetchone()[0] == 1

    def test_insert_duplicate_is_ignored(self, storage):
        article = _make_article()
        storage.insert_article(article)
        storage.insert_article(article)  # duplicate → silently ignored

        cursor = storage.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        assert cursor.fetchone()[0] == 1

    def test_insert_article_stores_all_fields(self, storage):
        article = _make_article(
            title="Full Article",
            url="https://example.com/full",
            source="Full Source",
            published_at=datetime(2024, 5, 20, 8, 0, 0),
            raw_text="Some raw content.",
            summary="Short summary.",
            topics=["tech", "ai"],
        )
        storage.insert_article(article)

        cursor = storage.conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE id = ?", (article.id,))
        row = cursor.fetchone()

        assert row["title"] == "Full Article"
        assert row["source"] == "Full Source"
        assert row["summary"] == "Short summary."
        assert row["raw_text"] == "Some raw content."
        assert "tech" in row["topics"]

    def test_insert_article_with_null_optional_fields(self, storage):
        article = _make_article(raw_text=None, summary=None, topics=[])
        storage.insert_article(article)

        cursor = storage.conn.cursor()
        cursor.execute(
            "SELECT summary, raw_text FROM articles WHERE id = ?", (article.id,)
        )
        row = cursor.fetchone()
        assert row["summary"] is None
        assert row["raw_text"] is None


class TestExistsArticle:
    def test_returns_true_for_existing_article(self, storage):
        article = _make_article()
        storage.insert_article(article)
        assert storage.exists_article(article.id) is True

    def test_returns_false_for_missing_article(self, storage):
        assert storage.exists_article("nonexistent-id") is False


class TestGetRecentArticles:
    def test_returns_empty_list_when_no_articles(self, storage):
        assert storage.get_recent_articles() == []

    def test_returns_inserted_articles(self, storage):
        article = _make_article()
        storage.insert_article(article)
        results = storage.get_recent_articles()
        assert len(results) == 1
        assert results[0].id == article.id

    def test_orders_by_published_at_desc(self, storage):
        older = _make_article(
            url="https://example.com/older",
            published_at=datetime(2024, 1, 1),
        )
        newer = _make_article(
            url="https://example.com/newer",
            published_at=datetime(2024, 6, 1),
        )
        storage.insert_article(older)
        storage.insert_article(newer)

        results = storage.get_recent_articles()
        assert results[0].id == newer.id
        assert results[1].id == older.id

    def test_limit_is_respected(self, storage):
        for i in range(5):
            storage.insert_article(
                _make_article(
                    url=f"https://example.com/{i}",
                    published_at=datetime(2024, 1, i + 1),
                )
            )
        results = storage.get_recent_articles(limit=3)
        assert len(results) == 3

    def test_returns_article_with_correct_types(self, storage):
        article = _make_article(
            topics=["python", "testing"],
            summary="A summary.",
            raw_text="Raw text.",
        )
        storage.insert_article(article)
        result = storage.get_recent_articles()[0]

        assert isinstance(result, Article)
        assert isinstance(result.published_at, datetime)
        assert isinstance(result.fetched_at, datetime)
        assert result.topics == ["python", "testing"]

    def test_returns_article_with_empty_topics_when_topics_null(self, storage):
        article = _make_article(topics=[])
        storage.insert_article(article)

        # Manually insert a row with NULL topics to exercise the None branch
        cursor = storage.conn.cursor()
        cursor.execute(
            "INSERT INTO articles (id, title, url, source, published_at, fetched_at, topics) "
            "VALUES (?, ?, ?, ?, ?, ?, NULL)",
            (
                "null-topics-id",
                "Null Topics",
                "https://example.com/null",
                "S",
                "2024-01-01T00:00:00",
                "2024-01-01T00:00:00",
            ),
        )
        storage.conn.commit()

        results = {r.id: r for r in storage.get_recent_articles(limit=20)}
        assert results["null-topics-id"].topics == []


class TestGetArticleById:
    def test_returns_article_when_found(self, storage):
        article = _make_article(
            title="By ID",
            url="https://example.com/byid",
            summary="Summary",
            raw_text="Raw",
            topics=["a", "b"],
        )
        storage.insert_article(article)
        result = storage.get_article_by_id(article.id)

        assert result is not None
        assert isinstance(result, Article)
        assert result.id == article.id
        assert result.title == "By ID"
        assert result.summary == "Summary"
        assert result.raw_text == "Raw"
        assert result.topics == ["a", "b"]

    def test_returns_none_when_not_found(self, storage):
        assert storage.get_article_by_id("does-not-exist") is None

    def test_returns_article_with_correct_datetime_types(self, storage):
        article = _make_article(url="https://example.com/dt")
        storage.insert_article(article)
        result = storage.get_article_by_id(article.id)

        assert isinstance(result.published_at, datetime)
        assert isinstance(result.fetched_at, datetime)

    def test_returns_empty_topics_when_null(self, storage):
        cursor = storage.conn.cursor()
        cursor.execute(
            "INSERT INTO articles (id, title, url, source, published_at, fetched_at, topics) "
            "VALUES (?, ?, ?, ?, ?, ?, NULL)",
            ("null-id", "T", "https://example.com/null2", "S",
             "2024-01-01T00:00:00", "2024-01-01T00:00:00"),
        )
        storage.conn.commit()

        result = storage.get_article_by_id("null-id")
        assert result.topics == []


class TestClose:
    def test_close_does_not_raise(self):
        store = SQLiteStorage(db_path=":memory:")
        store.close()  # should not raise
