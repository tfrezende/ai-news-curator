"""
Pytest configuration and shared fixtures for ai-news-curator tests.

Sets up environment variables and mocks before any src module is imported,
so that module-level side effects in server.py are safe to run in tests.
"""

import os
import sys
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Environment variables — must be set before src.config is first imported
# ---------------------------------------------------------------------------
os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
os.environ.setdefault("CHROMA_DB_PATH", "/tmp/test_chroma_ai_news")
os.environ.setdefault("NEWSAPI_KEY", "test_key")
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("FASTMCP_LOG_LEVEL", "WARNING")
os.environ.setdefault("LOG_LEVEL", "WARNING")

# ---------------------------------------------------------------------------
# Mock chromadb at the sys.modules level before src.storage.chroma is
# imported. This prevents real ChromaDB on-disk creation during tests and
# makes all chroma tests fast and side-effect free.
# ---------------------------------------------------------------------------
_mock_chroma_collection = MagicMock(name="chroma_collection")
_mock_chroma_client = MagicMock(name="chroma_client")
_mock_chroma_client.get_or_create_collection.return_value = _mock_chroma_collection

_mock_chromadb_module = MagicMock(name="chromadb_module")
_mock_chromadb_module.PersistentClient.return_value = _mock_chroma_client

sys.modules["chromadb"] = _mock_chromadb_module
