"""Unit tests for BaseFetcher (src/fetchers/base.py)."""

from src.fetchers.base import BaseFetcher
from src.models import Article


class ConcreteFetcher(BaseFetcher):
    """Minimal concrete implementation used only in tests."""

    @property
    def source_name(self) -> str:
        return super().source_name  # exercises the abstract body

    def fetch(self) -> list[Article]:
        return super().fetch()  # exercises the abstract body


class TestBaseFetcher:
    def test_source_name_abstract_body_is_covered(self):
        # Calls super() to execute the abstract method body for coverage.
        # The body is `...` which evaluates but has no return, so None is returned.
        fetcher = ConcreteFetcher()
        result = fetcher.source_name
        assert result is None

    def test_fetch_abstract_body_is_covered(self):
        fetcher = ConcreteFetcher()
        result = fetcher.fetch()
        assert result is None

    def test_concrete_subclass_instantiates(self):
        fetcher = ConcreteFetcher()
        assert isinstance(fetcher, BaseFetcher)
