"""Unit tests for IngestPipeline (src/pipeline/ingest.py)."""

import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.models import Article
from src.pipeline.ingest import IngestPipeline


def _make_article(**overrides) -> Article:
    defaults = dict(
        title="Pipeline Article",
        url="https://example.com/pipeline/1",
        source="Hacker News",
        published_at=datetime(2024, 5, 1, 12, 0, 0),
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
def pipeline(sql_storage, chroma_storage):
    return IngestPipeline(sql_storage=sql_storage, chroma_storage=chroma_storage)


class TestIngestPipelineInit:
    def test_stores_sql_and_chroma_storage(self, sql_storage, chroma_storage):
        p = IngestPipeline(sql_storage=sql_storage, chroma_storage=chroma_storage)
        assert p.sql_storage is sql_storage
        assert p.chroma_storage is chroma_storage

    def test_initializes_with_hackernews_fetcher(self, pipeline):
        from src.fetchers.hackernews import HackerNewsFetcher

        assert len(pipeline.fetchers) == 1
        assert isinstance(pipeline.fetchers[0], HackerNewsFetcher)


class TestIngestPipelineRun:
    def test_new_article_is_stored_in_both_backends(
        self, pipeline, sql_storage, chroma_storage
    ):
        article = _make_article()
        sql_storage.exists_article.return_value = False

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = [article]
        mock_fetcher.source_name = "Hacker News"
        pipeline.fetchers = [mock_fetcher]

        with patch("src.pipeline.ingest.fetch_article_content", return_value="content"):
            pipeline.run()

        sql_storage.insert_article.assert_called_once()
        chroma_storage.insert_article.assert_called_once()

    def test_existing_article_is_skipped(self, pipeline, sql_storage, chroma_storage):
        article = _make_article()
        sql_storage.exists_article.return_value = True

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = [article]
        mock_fetcher.source_name = "Hacker News"
        pipeline.fetchers = [mock_fetcher]

        with patch("src.pipeline.ingest.fetch_article_content"):
            pipeline.run()

        sql_storage.insert_article.assert_not_called()
        chroma_storage.insert_article.assert_not_called()

    def test_article_content_is_fetched_and_attached(
        self, pipeline, sql_storage, chroma_storage
    ):
        article = _make_article()
        sql_storage.exists_article.return_value = False

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = [article]
        mock_fetcher.source_name = "Hacker News"
        pipeline.fetchers = [mock_fetcher]

        with patch(
            "src.pipeline.ingest.fetch_article_content", return_value="fetched content"
        ) as mock_fetch:
            pipeline.run()

        mock_fetch.assert_called_once_with(article.url)
        stored_article = sql_storage.insert_article.call_args[0][0]
        assert stored_article.raw_text == "fetched content"

    def test_article_content_none_when_fetch_fails(
        self, pipeline, sql_storage, chroma_storage
    ):
        article = _make_article()
        sql_storage.exists_article.return_value = False

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = [article]
        mock_fetcher.source_name = "Hacker News"
        pipeline.fetchers = [mock_fetcher]

        with patch("src.pipeline.ingest.fetch_article_content", return_value=None):
            pipeline.run()

        stored_article = sql_storage.insert_article.call_args[0][0]
        assert stored_article.raw_text is None

    def test_storage_error_is_caught_and_pipeline_continues(
        self, pipeline, sql_storage, chroma_storage, caplog
    ):
        article_a = _make_article(url="https://example.com/a")
        article_b = _make_article(url="https://example.com/b")

        sql_storage.exists_article.return_value = False
        sql_storage.insert_article.side_effect = [Exception("DB error"), None]

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = [article_a, article_b]
        mock_fetcher.source_name = "Hacker News"
        pipeline.fetchers = [mock_fetcher]

        with patch("src.pipeline.ingest.fetch_article_content", return_value="content"):
            with caplog.at_level(logging.ERROR, logger="src.pipeline.ingest"):
                pipeline.run()

        assert "Error storing article" in caplog.text
        # second article still processed
        assert sql_storage.insert_article.call_count == 2

    def test_fetcher_error_is_caught_and_pipeline_continues(
        self, pipeline, sql_storage, chroma_storage, caplog
    ):
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = Exception("Network failure")
        mock_fetcher.source_name = "Hacker News"
        pipeline.fetchers = [mock_fetcher]

        with caplog.at_level(logging.ERROR, logger="src.pipeline.ingest"):
            pipeline.run()

        assert "Error processing fetcher" in caplog.text
        sql_storage.insert_article.assert_not_called()

    def test_multiple_fetchers_are_all_run(self, pipeline, sql_storage, chroma_storage):
        article_a = _make_article(url="https://example.com/a")
        article_b = _make_article(url="https://example.com/b")

        sql_storage.exists_article.return_value = False

        fetcher_a = MagicMock()
        fetcher_a.fetch.return_value = [article_a]
        fetcher_a.source_name = "Source A"

        fetcher_b = MagicMock()
        fetcher_b.fetch.return_value = [article_b]
        fetcher_b.source_name = "Source B"

        pipeline.fetchers = [fetcher_a, fetcher_b]

        with patch("src.pipeline.ingest.fetch_article_content", return_value="content"):
            pipeline.run()

        assert sql_storage.insert_article.call_count == 2

    def test_run_with_no_articles_is_a_noop(
        self, pipeline, sql_storage, chroma_storage
    ):
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = []
        mock_fetcher.source_name = "Empty Source"
        pipeline.fetchers = [mock_fetcher]

        pipeline.run()

        sql_storage.insert_article.assert_not_called()
        chroma_storage.insert_article.assert_not_called()
