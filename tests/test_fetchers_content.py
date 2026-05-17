"""Unit tests for fetch_article_content (src/fetchers/content.py)."""

import logging
from unittest.mock import MagicMock, patch

import httpx

from src.fetchers.content import fetch_article_content


def _make_httpx_response(html: str, status_code: int = 200) -> MagicMock:
    response = MagicMock(spec=httpx.Response)
    response.text = html
    response.status_code = status_code
    response.raise_for_status = MagicMock()
    return response


class TestFetchArticleContentSuccess:
    def test_returns_text_content_from_html(self):
        html = "<html><body><p>Hello world</p></body></html>"
        response = _make_httpx_response(html)

        with patch("src.fetchers.content.httpx.get", return_value=response):
            result = fetch_article_content("https://example.com/article")

        assert result is not None
        assert "Hello world" in result

    def test_strips_script_tags(self):
        html = (
            "<html><body><p>Article text</p><script>alert('x')</script></body></html>"
        )
        response = _make_httpx_response(html)

        with patch("src.fetchers.content.httpx.get", return_value=response):
            result = fetch_article_content("https://example.com")

        assert "alert" not in result
        assert "Article text" in result

    def test_strips_style_tags(self):
        html = (
            "<html><body><p>Content</p><style>.foo { color: red }</style></body></html>"
        )
        response = _make_httpx_response(html)

        with patch("src.fetchers.content.httpx.get", return_value=response):
            result = fetch_article_content("https://example.com")

        assert "color" not in result
        assert "Content" in result

    def test_strips_nav_header_footer_aside(self):
        html = (
            "<html><body>"
            "<header>Site Header</header>"
            "<nav>Navigation</nav>"
            "<aside>Sidebar</aside>"
            "<footer>Footer</footer>"
            "<p>Main content</p>"
            "</body></html>"
        )
        response = _make_httpx_response(html)

        with patch("src.fetchers.content.httpx.get", return_value=response):
            result = fetch_article_content("https://example.com")

        assert "Main content" in result
        assert "Site Header" not in result
        assert "Navigation" not in result
        assert "Sidebar" not in result
        assert "Footer" not in result

    def test_passes_timeout_to_httpx_get(self):
        html = "<html><body><p>text</p></body></html>"
        response = _make_httpx_response(html)

        with patch("src.fetchers.content.httpx.get", return_value=response) as mock_get:
            fetch_article_content("https://example.com")

        mock_get.assert_called_once_with("https://example.com", timeout=10)


class TestFetchArticleContentErrors:
    def test_returns_none_on_http_error(self, caplog):
        with patch(
            "src.fetchers.content.httpx.get",
            side_effect=httpx.HTTPError("404 Not Found"),
        ):
            with caplog.at_level(logging.WARNING, logger="src.fetchers.content"):
                result = fetch_article_content("https://example.com/missing")

        assert result is None
        assert "HTTP error fetching" in caplog.text

    def test_returns_none_on_unexpected_exception(self, caplog):
        with patch(
            "src.fetchers.content.httpx.get",
            side_effect=RuntimeError("connection refused"),
        ):
            with caplog.at_level(logging.WARNING, logger="src.fetchers.content"):
                result = fetch_article_content("https://example.com")

        assert result is None
        assert "Error fetching content from" in caplog.text
