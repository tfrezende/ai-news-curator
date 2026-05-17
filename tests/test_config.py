"""Unit tests for the Settings configuration (src/config.py)."""


from src.config import Settings


class TestSettingsDefaults:
    """Settings fields default to None when no env vars are set."""

    def test_all_fields_default_to_none(self, monkeypatch):
        for key in (
            "NEWSAPI_KEY",
            "OLLAMA_BASE_URL",
            "CHROMA_DB_PATH",
            "SQLITE_DB_PATH",
            "FASTMCP_LOG_LEVEL",
            "LOG_LEVEL",
        ):
            monkeypatch.delenv(key, raising=False)

        s = Settings(_env_file=None)

        assert s.NEWSAPI_KEY is None
        assert s.OLLAMA_BASE_URL is None
        assert s.CHROMA_DB_PATH is None
        assert s.SQLITE_DB_PATH is None
        assert s.FASTMCP_LOG_LEVEL is None
        assert s.LOG_LEVEL is None


class TestSettingsFromEnv:
    """Settings fields are populated from environment variables."""

    def test_newsapi_key_loaded_from_env(self, monkeypatch):
        monkeypatch.setenv("NEWSAPI_KEY", "my-api-key")
        s = Settings(_env_file=None)
        assert s.NEWSAPI_KEY == "my-api-key"

    def test_ollama_base_url_loaded_from_env(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
        s = Settings(_env_file=None)
        assert s.OLLAMA_BASE_URL == "http://ollama:11434"

    def test_chroma_db_path_loaded_from_env(self, monkeypatch):
        monkeypatch.setenv("CHROMA_DB_PATH", "/data/chroma")
        s = Settings(_env_file=None)
        assert s.CHROMA_DB_PATH == "/data/chroma"

    def test_sqlite_db_path_loaded_from_env(self, monkeypatch):
        monkeypatch.setenv("SQLITE_DB_PATH", "/data/news.db")
        s = Settings(_env_file=None)
        assert s.SQLITE_DB_PATH == "/data/news.db"

    def test_fastmcp_log_level_loaded_from_env(self, monkeypatch):
        monkeypatch.setenv("FASTMCP_LOG_LEVEL", "DEBUG")
        s = Settings(_env_file=None)
        assert s.FASTMCP_LOG_LEVEL == "DEBUG"

    def test_log_level_loaded_from_env(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "ERROR")
        s = Settings(_env_file=None)
        assert s.LOG_LEVEL == "ERROR"

    def test_module_level_settings_instance_exists(self):
        from src.config import settings

        assert isinstance(settings, Settings)
