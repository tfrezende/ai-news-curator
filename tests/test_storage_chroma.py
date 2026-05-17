"""Unit tests for ChromaStorage (src/storage/chroma.py)."""

import json
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.models import Article
from src.storage.chroma import ChromaStorage


def _make_article(**overrides) -> Article:
    defaults = dict(
        title="Chroma Article",
        url="https://example.com/chroma/1",
        source="Chroma News",
        published_at=datetime(2024, 4, 1, 8, 0, 0),
    )
    defaults.update(overrides)
    return Article(**defaults)


@pytest.fixture
def mock_collection():
    return MagicMock(name="collection")


@pytest.fixture
def mock_client(mock_collection):
    client = MagicMock(name="client")
    client.get_or_create_collection.return_value = mock_collection
    return client


@pytest.fixture
def chroma_storage(mock_client, monkeypatch):
    """Return a ChromaStorage instance backed by mocked chromadb."""
    import src.storage.chroma as chroma_module

    monkeypatch.setattr(
        chroma_module.chromadb, "PersistentClient", lambda path: mock_client
    )
    storage = ChromaStorage(db_path="/tmp/test_chroma")
    return storage


class TestChromaStorageInit:
    def test_creates_collection_on_init(self, mock_client):

        mock_client.get_or_create_collection.return_value = MagicMock()

        storage = ChromaStorage.__new__(ChromaStorage)
        storage.client = mock_client
        storage.collection = mock_client.get_or_create_collection(name="articles")

        mock_client.get_or_create_collection.assert_called_with(name="articles")

    def test_default_collection_name_is_articles(self, mock_client, monkeypatch):
        import src.storage.chroma as chroma_module

        monkeypatch.setattr(
            chroma_module.chromadb, "PersistentClient", lambda path: mock_client
        )
        ChromaStorage(db_path="/tmp/test")
        mock_client.get_or_create_collection.assert_called_with(name="articles")

    def test_custom_collection_name(self, mock_client, monkeypatch):
        import src.storage.chroma as chroma_module

        monkeypatch.setattr(
            chroma_module.chromadb, "PersistentClient", lambda path: mock_client
        )
        ChromaStorage(db_path="/tmp/test", collection_name="custom")
        mock_client.get_or_create_collection.assert_called_with(name="custom")


class TestInsertArticle:
    def test_insert_calls_collection_add(self, chroma_storage, mock_collection):
        article = _make_article()
        chroma_storage.insert_article(article)
        mock_collection.add.assert_called_once()

    def test_insert_passes_correct_id(self, chroma_storage, mock_collection):
        article = _make_article()
        chroma_storage.insert_article(article)
        _, kwargs = mock_collection.add.call_args
        assert kwargs["ids"] == [article.id]

    def test_insert_passes_raw_text_as_document(self, chroma_storage, mock_collection):
        article = _make_article(raw_text="This is raw text.")
        chroma_storage.insert_article(article)
        _, kwargs = mock_collection.add.call_args
        assert kwargs["documents"] == ["This is raw text."]

    def test_insert_uses_empty_string_when_raw_text_is_none(
        self, chroma_storage, mock_collection
    ):
        article = _make_article(raw_text=None)
        chroma_storage.insert_article(article)
        _, kwargs = mock_collection.add.call_args
        assert kwargs["documents"] == [""]

    def test_insert_metadata_fields(self, chroma_storage, mock_collection):
        published = datetime(2024, 4, 1, 8, 0, 0)
        article = _make_article(
            title="Meta Title",
            source="Meta Source",
            published_at=published,
            summary="Meta summary",
            raw_text="Meta raw text",
            topics=["a", "b"],
        )
        chroma_storage.insert_article(article)
        _, kwargs = mock_collection.add.call_args
        metadata = kwargs["metadatas"][0]

        assert metadata["title"] == "Meta Title"
        assert metadata["source"] == "Meta Source"
        assert metadata["summary"] == "Meta summary"
        assert metadata["raw_text"] == "Meta raw text"
        assert json.loads(metadata["topics"]) == ["a", "b"]
        assert metadata["published_at"] == published.isoformat()

    def test_insert_uses_empty_string_when_summary_is_none(
        self, chroma_storage, mock_collection
    ):
        article = _make_article(summary=None)
        chroma_storage.insert_article(article)
        _, kwargs = mock_collection.add.call_args
        assert kwargs["metadatas"][0]["summary"] == ""

    def test_insert_uses_empty_topics_list(self, chroma_storage, mock_collection):
        article = _make_article(topics=[])
        chroma_storage.insert_article(article)
        _, kwargs = mock_collection.add.call_args
        assert json.loads(kwargs["metadatas"][0]["topics"]) == []


class TestSearchArticles:
    def _setup_query_result(self, mock_collection, ids, metadatas, distances):
        mock_collection.query.return_value = {
            "ids": [ids],
            "metadatas": [metadatas],
            "distances": [distances],
        }

    def test_search_returns_list_of_dicts(self, chroma_storage, mock_collection):
        self._setup_query_result(
            mock_collection,
            ids=["id1"],
            metadatas=[
                {"title": "T1", "url": "http://u1", "source": "S1", "summary": "Sum1"}
            ],
            distances=[0.2],
        )
        results = chroma_storage.search_articles("test query")
        assert isinstance(results, list)
        assert len(results) == 1

    def test_search_result_fields(self, chroma_storage, mock_collection):
        self._setup_query_result(
            mock_collection,
            ids=["abc123"],
            metadatas=[
                {
                    "title": "Article A",
                    "url": "https://a.com",
                    "source": "SrcA",
                    "summary": "Sum A",
                }
            ],
            distances=[0.1],
        )
        result = chroma_storage.search_articles("query")[0]

        assert result["id"] == "abc123"
        assert result["title"] == "Article A"
        assert result["url"] == "https://a.com"
        assert result["source"] == "SrcA"
        assert result["summary"] == "Sum A"
        assert result["score"] == round(1 - 0.1, 3)

    def test_search_score_is_rounded(self, chroma_storage, mock_collection):
        self._setup_query_result(
            mock_collection,
            ids=["x"],
            metadatas=[{"title": "T", "url": "u", "source": "s", "summary": ""}],
            distances=[0.33333],
        )
        result = chroma_storage.search_articles("q")[0]
        assert result["score"] == round(1 - 0.33333, 3)

    def test_search_passes_n_results_to_query(self, chroma_storage, mock_collection):
        mock_collection.query.return_value = {
            "ids": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        chroma_storage.search_articles("q", n_results=5)
        mock_collection.query.assert_called_once_with(query_texts=["q"], n_results=5)

    def test_search_default_n_results_is_10(self, chroma_storage, mock_collection):
        mock_collection.query.return_value = {
            "ids": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        chroma_storage.search_articles("q")
        mock_collection.query.assert_called_once_with(query_texts=["q"], n_results=10)

    def test_search_returns_empty_list_when_no_results(
        self, chroma_storage, mock_collection
    ):
        mock_collection.query.return_value = {
            "ids": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        results = chroma_storage.search_articles("nothing")
        assert results == []

    def test_search_multiple_results(self, chroma_storage, mock_collection):
        self._setup_query_result(
            mock_collection,
            ids=["id1", "id2"],
            metadatas=[
                {"title": "T1", "url": "u1", "source": "s1", "summary": ""},
                {"title": "T2", "url": "u2", "source": "s2", "summary": ""},
            ],
            distances=[0.1, 0.3],
        )
        results = chroma_storage.search_articles("multi")
        assert len(results) == 2
        assert results[0]["id"] == "id1"
        assert results[1]["id"] == "id2"


class TestClose:
    def test_close_calls_client_close(self, chroma_storage, mock_client):
        chroma_storage.close()
        mock_client.close.assert_called_once()
