"""Unit tests for the MCP server tools (src/server.py)."""

import runpy
from unittest.mock import MagicMock, patch

import src.server as server_module
from src.server import health_check


class TestHealthCheck:
    def test_returns_ok_status_when_both_storages_exist(self):
        with (
            patch.object(server_module, "sql_storage", MagicMock()),
            patch.object(server_module, "chroma_storage", MagicMock()),
        ):
            result = health_check()

        assert result["status"] == "ok"
        assert result["message"] == "AI News Curator is running!"
        assert result["sqlite_status"] == "ok"
        assert result["chroma_status"] == "ok"

    def test_sqlite_status_is_error_when_sql_storage_is_none(self):
        with (
            patch.object(server_module, "sql_storage", None),
            patch.object(server_module, "chroma_storage", MagicMock()),
        ):
            result = health_check()

        assert result["sqlite_status"] == "error"
        assert result["chroma_status"] == "ok"

    def test_chroma_status_is_error_when_chroma_storage_is_none(self):
        with (
            patch.object(server_module, "sql_storage", MagicMock()),
            patch.object(server_module, "chroma_storage", None),
        ):
            result = health_check()

        assert result["sqlite_status"] == "ok"
        assert result["chroma_status"] == "error"

    def test_both_statuses_are_error_when_both_storages_are_none(self):
        with (
            patch.object(server_module, "sql_storage", None),
            patch.object(server_module, "chroma_storage", None),
        ):
            result = health_check()

        assert result["sqlite_status"] == "error"
        assert result["chroma_status"] == "error"

    def test_return_value_contains_all_expected_keys(self):
        result = health_check()
        assert set(result.keys()) == {
            "status",
            "message",
            "sqlite_status",
            "chroma_status",
        }


class TestMainBlock:
    def test_main_calls_mcp_run(self):
        from fastmcp import FastMCP

        with patch.object(FastMCP, "run") as mock_run:
            runpy.run_module("src.server", run_name="__main__")

        mock_run.assert_called_once()
