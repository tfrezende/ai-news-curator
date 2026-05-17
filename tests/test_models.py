"""Unit tests for the Article model (src/models.py)."""

import hashlib
from datetime import datetime

import pytest

from src.models import Article


class TestArticleIdGeneration:
    """Tests for the set_id_from_url model validator."""

    def test_id_generated_from_url_when_not_provided(self):
        article = Article(
            title="Test Article",
            url="https://example.com/news/1",
            source="Example News",
            published_at=datetime(2024, 1, 15, 10, 0, 0),
        )

        expected_id = hashlib.sha256(
            b"https://example.com/news/1"
        ).hexdigest()
        assert article.id == expected_id

    def test_existing_id_is_preserved(self):
        custom_id = "my-custom-id-123"
        article = Article(
            title="Test Article",
            url="https://example.com/news/1",
            source="Example News",
            published_at=datetime(2024, 1, 15, 10, 0, 0),
            id=custom_id,
        )

        assert article.id == custom_id

    def test_empty_url_does_not_generate_id(self):
        article = Article(
            title="Test Article",
            url="",
            source="Example News",
            published_at=datetime(2024, 1, 15, 10, 0, 0),
        )

        assert article.id is None


class TestArticleDefaults:
    """Tests for default field values."""

    def test_topics_defaults_to_empty_list(self):
        article = Article(
            title="Test",
            url="https://example.com/1",
            source="Source",
            published_at=datetime(2024, 1, 1),
        )

        assert article.topics == []

    def test_fetched_at_defaults_to_now(self):
        before = datetime.now()
        article = Article(
            title="Test",
            url="https://example.com/2",
            source="Source",
            published_at=datetime(2024, 1, 1),
        )
        after = datetime.now()

        assert before <= article.fetched_at <= after

    def test_raw_text_defaults_to_none(self):
        article = Article(
            title="Test",
            url="https://example.com/3",
            source="Source",
            published_at=datetime(2024, 1, 1),
        )

        assert article.raw_text is None

    def test_summary_defaults_to_none(self):
        article = Article(
            title="Test",
            url="https://example.com/4",
            source="Source",
            published_at=datetime(2024, 1, 1),
        )

        assert article.summary is None


class TestArticleFullConstruction:
    """Tests for fully-specified Article construction."""

    def test_all_fields_set_correctly(self):
        published = datetime(2024, 6, 1, 12, 0, 0)
        fetched = datetime(2024, 6, 1, 13, 0, 0)

        article = Article(
            title="Full Article",
            url="https://example.com/full",
            source="News Source",
            published_at=published,
            raw_text="Some raw text content.",
            summary="A short summary.",
            topics=["tech", "ai"],
            fetched_at=fetched,
            id="explicit-id",
        )

        assert article.title == "Full Article"
        assert article.url == "https://example.com/full"
        assert article.source == "News Source"
        assert article.published_at == published
        assert article.raw_text == "Some raw text content."
        assert article.summary == "A short summary."
        assert article.topics == ["tech", "ai"]
        assert article.fetched_at == fetched
        assert article.id == "explicit-id"

    def test_different_urls_produce_different_ids(self):
        article_a = Article(
            title="A",
            url="https://example.com/a",
            source="S",
            published_at=datetime(2024, 1, 1),
        )
        article_b = Article(
            title="B",
            url="https://example.com/b",
            source="S",
            published_at=datetime(2024, 1, 1),
        )

        assert article_a.id != article_b.id

    def test_same_url_produces_same_id(self):
        kwargs = dict(
            title="Same",
            url="https://example.com/same",
            source="S",
            published_at=datetime(2024, 1, 1),
        )
        assert Article(**kwargs).id == Article(**kwargs).id

    def test_required_field_missing_raises_validation_error(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Article(
                url="https://example.com", source="S", published_at=datetime(2024, 1, 1)
            )  # missing title
