from abc import ABC, abstractmethod

from src.models import Article


class BaseFetcher(ABC):
    """Abstract base class for news fetchers."""

    @abstractmethod
    def fetch(self) -> list[Article]:
        """Fetch articles from the source and return a list of Article objects."""
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name identifier for the news source (e.g. 'NewsAPI', 'RSS Feed')."""
        ...
