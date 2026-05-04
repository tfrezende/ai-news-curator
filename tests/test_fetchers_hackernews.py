"""Unit tests for HackerNewsFetcher (src/fetchers/hackernews.py)."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.fetchers.hackernews import HackerNewsFetcher
from src.models import Article

STORY_TIME = 1700000000  # fixed Unix timestamp for tests


@pytest.fixture
def fetcher():
    return HackerNewsFetcher()


def _make_story(
    story_id: int, title: str = "Test Story", url: str = "https://example.com"
) -> dict:
    return {"id": story_id, "title": title, "url": url, "time": STORY_TIME}


def _mock_response(json_data) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


class TestSourceName:
    def test_source_name_is_hacker_news(self, fetcher):
        assert fetcher.source_name == "Hacker News"


class TestFetchSuccess:
    def test_returns_list_of_articles(self, fetcher):
        responses = [
            _mock_response([1]),
            _mock_response(_make_story(1)),
        ]
        with patch("httpx.get", side_effect=responses):
            articles = fetcher.fetch()

        assert len(articles) == 1
        assert isinstance(articles[0], Article)

    def test_article_fields_are_mapped_correctly(self, fetcher):
        responses = [
            _mock_response([42]),
            _mock_response(
                _make_story(42, title="My Title", url="https://news.example.com/post")
            ),
        ]
        with patch("httpx.get", side_effect=responses):
            articles = fetcher.fetch()

        assert articles[0].title == "My Title"
        assert articles[0].url == "https://news.example.com/post"
        assert articles[0].source == "Hacker News"
        assert articles[0].published_at == datetime.fromtimestamp(STORY_TIME)

    def test_default_limit_is_30(self, fetcher):
        story_ids = list(range(1, 40))  # 39 IDs returned by the API

        def make_response(url, *args, **kwargs):
            if "topstories" in url:
                return _mock_response(story_ids)
            story_id = int(url.split("/")[-1].replace(".json", ""))
            return _mock_response(_make_story(story_id))

        with patch("httpx.get", side_effect=make_response):
            articles = fetcher.fetch()

        assert len(articles) == 30

    def test_custom_limit_is_respected(self, fetcher):
        story_ids = list(range(1, 40))

        def make_response(url, *args, **kwargs):
            if "topstories" in url:
                return _mock_response(story_ids)
            story_id = int(url.split("/")[-1].replace(".json", ""))
            return _mock_response(_make_story(story_id))

        with patch("httpx.get", side_effect=make_response):
            articles = fetcher.fetch(limit=5)

        assert len(articles) == 5

    def test_skips_stories_without_url(self, fetcher):
        responses = [
            _mock_response([1, 2]),
            _mock_response(_make_story(1)),
            _mock_response({"id": 2, "title": "Ask HN: No URL", "time": STORY_TIME}),
        ]
        with patch("httpx.get", side_effect=responses):
            articles = fetcher.fetch()

        assert len(articles) == 1

    def test_skips_stories_without_title(self, fetcher):
        responses = [
            _mock_response([1]),
            _mock_response({"id": 1, "url": "https://x.com", "time": STORY_TIME}),
        ]
        with patch("httpx.get", side_effect=responses):
            articles = fetcher.fetch()

        assert articles == []

    def test_skips_stories_without_time(self, fetcher):
        responses = [
            _mock_response([1]),
            _mock_response({"id": 1, "title": "No time", "url": "https://x.com"}),
        ]
        with patch("httpx.get", side_effect=responses):
            articles = fetcher.fetch()

        assert articles == []

    def test_skips_none_story_data(self, fetcher):
        responses = [
            _mock_response([1]),
            _mock_response(None),
        ]
        with patch("httpx.get", side_effect=responses):
            articles = fetcher.fetch()

        assert articles == []


class TestFetchErrors:
    def test_http_error_on_individual_story_is_skipped(self, fetcher, caplog):
        import logging

        bad_resp = MagicMock(spec=httpx.Response)
        bad_resp.raise_for_status.side_effect = httpx.HTTPError("500")

        responses = [
            _mock_response([1, 2]),
            bad_resp,  # story 1 → HTTPError
            _mock_response(_make_story(2)),  # story 2 → ok
        ]
        with patch("httpx.get", side_effect=responses):
            with caplog.at_level(logging.WARNING, logger="src.fetchers.hackernews"):
                articles = fetcher.fetch()

        assert len(articles) == 1
        assert "Error fetching story" in caplog.text

    def test_http_error_on_top_stories_propagates(self, fetcher):
        top_resp = MagicMock(spec=httpx.Response)
        top_resp.raise_for_status.side_effect = httpx.HTTPError("503")

        with patch("httpx.get", return_value=top_resp):
            with pytest.raises(httpx.HTTPError):
                fetcher.fetch()


class TestIsValidStory:
    def test_valid_story_returns_true(self, fetcher):
        assert fetcher._is_valid_story(_make_story(1)) is True

    def test_none_returns_false(self, fetcher):
        assert not fetcher._is_valid_story(None)

    def test_missing_title_returns_false(self, fetcher):
        assert (
            fetcher._is_valid_story({"url": "https://x.com", "time": STORY_TIME})
            is False
        )

    def test_missing_url_returns_false(self, fetcher):
        assert fetcher._is_valid_story({"title": "T", "time": STORY_TIME}) is False

    def test_none_time_returns_false(self, fetcher):
        assert (
            fetcher._is_valid_story(
                {"title": "T", "url": "https://x.com", "time": None}
            )
            is False
        )
