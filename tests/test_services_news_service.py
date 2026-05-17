"""Unit tests for NewsService (src/services/news_service.py)."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.models import Article
from src.services.news_service import NewsService


def _make_article(**overrides) -> Article:
    defaults = dict(
        title="Service Article",
        url="https://example.com/service/1",
        source="Example",
        published_at=datetime(2024, 6, 1, 12, 0, 0),
    )
    defaults.update(overrides)
    return Article(**defaults)


@pytest.fixture
def sql_storage():
    return MagicMock(name="sql_storage")


@pytest.fixture
def chroma_storage():
    return MagicMock(name="chroma_storage")


@pytest.fixture
def service(sql_storage, chroma_storage):
    return NewsService(sql_storage=sql_storage, chroma_storage=chroma_storage)


class TestNewsServiceInit:
    def test_stores_both_backends(self, sql_storage, chroma_storage):
        svc = NewsService(sql_storage=sql_storage, chroma_storage=chroma_storage)
        assert svc.sql_storage is sql_storage
        assert svc.chroma_storage is chroma_storage


class TestSearchNews:
    def test_delegates_to_chroma_search(self, service, chroma_storage):
        chroma_storage.search_articles.return_value = [{"id": "x", "title": "T"}]
        result = service.search_news("AI news")
        chroma_storage.search_articles.assert_called_once_with("AI news", limit=10)
        assert result == [{"id": "x", "title": "T"}]

    def test_custom_limit_is_passed_through(self, service, chroma_storage):
        chroma_storage.search_articles.return_value = []
        service.search_news("query", limit=5)
        chroma_storage.search_articles.assert_called_once_with("query", limit=5)

    def test_returns_empty_list_when_no_results(self, service, chroma_storage):
        chroma_storage.search_articles.return_value = []
        assert service.search_news("nothing") == []


class TestGetArticle:
    def test_delegates_to_sql_get_by_id(self, service, sql_storage):
        article = _make_article()
        sql_storage.get_article_by_id.return_value = article
        result = service.get_article(article.id)
        sql_storage.get_article_by_id.assert_called_once_with(article.id)
        assert result is article

    def test_returns_none_when_article_not_found(self, service, sql_storage):
        sql_storage.get_article_by_id.return_value = None
        assert service.get_article("nonexistent") is None


class TestGetLatestArticles:
    def test_delegates_to_sql_get_recent(self, service, sql_storage):
        articles = [_make_article()]
        sql_storage.get_recent_articles.return_value = articles
        result = service.get_latest_articles()
        sql_storage.get_recent_articles.assert_called_once_with(limit=10)
        assert result is articles

    def test_custom_limit_is_passed_through(self, service, sql_storage):
        sql_storage.get_recent_articles.return_value = []
        service.get_latest_articles(limit=3)
        sql_storage.get_recent_articles.assert_called_once_with(limit=3)

    def test_returns_empty_list_when_no_articles(self, service, sql_storage):
        sql_storage.get_recent_articles.return_value = []
        assert service.get_latest_articles() == []
