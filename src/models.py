import hashlib
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class Article(BaseModel):
    """
    Represents a news article with various attributes such as title, URL, source, publication date, raw text, summary, topics, and fetched date. The Article model also includes a unique ID generated from the URL if not provided.
    Attributes:
        title (str): The title of the news article.
        url (str): The URL of the news article.
        source (str): The source or publisher of the news article.
        published_at (datetime): The publication date and time of the news article.
        raw_text (str | None): The raw text content of the news article, if available.
        summary (str | None): A summary of the news article, if available.
        topics (list[str]): A list of topics or keywords associated with the news article.
        fetched_at (datetime): The date and time when the article was fetched or processed.
        id (str | None): A unique identifier for the article, generated from the URL if not provided.
    """

    title: str
    url: str
    source: str
    published_at: datetime
    raw_text: str | None = None
    summary: str | None = None
    topics: list[str] = Field(default_factory=list)
    fetched_at: datetime = Field(default_factory=datetime.now)
    id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def set_id_from_url(cls, values: dict) -> dict:
        """
        Sets the ID of the article based on the URL if the ID is not already provided.
        Args:
            values (dict): A dictionary of values to initialize the Article model.
        Returns:
            dict: The updated dictionary with the ID set if it was not provided.
        """
        url = values.get("url")
        if url and not values.get("id"):
            values["id"] = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return values
