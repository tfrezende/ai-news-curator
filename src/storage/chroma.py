import json

import chromadb

from src.models import Article


class ChromaStorage:
    """
    ChromaStorage is a simple storage backend for the AI News Curator application that uses ChromaDB to store news articles. It provides methods to insert articles and search for articles based on a query.

    Attributes:
        db_path (str): The file path to the ChromaDB database.
        collection_name (str): The name of the collection in the ChromaDB database.
        client (chromadb.PersistentClient): The ChromaDB client object.
        collection (chromadb.Collection): The ChromaDB collection object.

    Methods:
        insert_article(article: Article) -> None: Inserts a new article into the ChromaDB collection.
        search_articles(query: str, n_results: int = 10) -> list[dict]: Searches for articles in the ChromaDB collection based on a query.
    """

    def __init__(
        self, db_path: str = "chroma_db", collection_name: str = "articles"
    ) -> None:
        """
        Initializes the ChromaStorage instance by setting the database path and collection name, and establishing a connection to the ChromaDB client.
        Args:
            db_path (str): The file path to the ChromaDB database. Defaults to "chroma_db".
            collection_name (str): The name of the collection in the ChromaDB database. Defaults to "articles".
        """
        self.client = chromadb.PersistentClient(path=str(db_path))
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def insert_article(self, article: Article) -> None:
        """
        Inserts a new article into the ChromaDB collection.
        Args:
            article (Article): The Article object to be inserted into the ChromaDB collection.
        """
        self.collection.add(
            ids=[article.id],
            metadatas=[
                {
                    "title": article.title,
                    "url": article.url,
                    "source": article.source,
                    "published_at": article.published_at.isoformat(),
                    "fetched_at": article.fetched_at.isoformat(),
                    "summary": article.summary or "",
                    "raw_text": article.raw_text or "",
                    "topics": json.dumps(article.topics or []),
                }
            ],
            documents=[article.raw_text or ""],
        )

    def search_articles(self, query: str, n_results: int = 10) -> list[dict]:
        """
        Searches for articles in the ChromaDB collection based on a query.
        Args:
            query (str): The query string to search for.
            n_results (int): The maximum number of search results to return. Defaults to 10.
        Returns:
            list[dict]: A list of dictionaries representing the search results.
        """
        results = self.collection.query(query_texts=[query], n_results=n_results)
        return [
            {
                "id": result_id,
                "title": metadata.get("title"),
                "url": metadata.get("url"),
                "source": metadata.get("source"),
                "summary": metadata.get("summary"),
                "score": round(1 - distance, 3),
            }
            for result_id, metadata, distance in zip(
                results["ids"][0], results["metadatas"][0], results["distances"][0],
                strict=False
            )
        ]

    def close(self) -> None:
        """Closes the ChromaDB client connection."""
        self.client.close()
