import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def fetch_article_content(url: str) -> str | None:
    """Fetches the raw text content of an article given its URL."""
    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
            tag.decompose()

        content = soup.get_text(separator=" ", strip=True)
        return content
    except httpx.HTTPError as e:
        logger.warning(f"HTTP error fetching {url}: {e}")
    except Exception as e:
        logger.warning(f"Error fetching content from {url}: {e}")
    return None
