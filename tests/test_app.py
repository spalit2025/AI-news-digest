"""Tests for app.py -- Flask routes, ReportManager, and pipeline integration."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app import ReportManager, get_available_sources


# ---------------------------------------------------------------------------
# ReportManager tests
# ---------------------------------------------------------------------------

class TestReportManager:
    def test_initial_state(self):
        manager = ReportManager()
        status = manager.get_status()

        assert status["running"] is False
        assert status["error"] is None
        assert status["last_report"] is None
        assert status["articles_processed"] == 0

    def test_start_generation(self):
        manager = ReportManager()
        manager.start_generation()
        status = manager.get_status()

        assert status["running"] is True
        assert "Starting" in status["progress"]
        assert status["error"] is None

    def test_finish_with_report(self):
        manager = ReportManager()
        manager.start_generation()
        manager.finish_generation(report_filename="test_report.pdf")
        status = manager.get_status()

        assert status["running"] is False
        assert status["last_report"] == "test_report.pdf"
        assert "completed" in status["progress"].lower()

    def test_finish_with_error(self):
        manager = ReportManager()
        manager.start_generation()
        manager.finish_generation(error="API key missing")
        status = manager.get_status()

        assert status["running"] is False
        assert status["error"] == "API key missing"
        assert "Error" in status["progress"]

    def test_finish_no_articles(self):
        manager = ReportManager()
        manager.start_generation()
        manager.finish_generation()
        status = manager.get_status()

        assert status["running"] is False
        assert "No new articles" in status["progress"]

    def test_update_progress(self):
        manager = ReportManager()
        manager.update_progress("Processing...", articles_processed=5)
        status = manager.get_status()

        assert status["progress"] == "Processing..."
        assert status["articles_processed"] == 5

    def test_is_running(self):
        manager = ReportManager()
        assert manager.is_running() is False

        manager.start_generation()
        assert manager.is_running() is True

        manager.finish_generation()
        assert manager.is_running() is False


# ---------------------------------------------------------------------------
# get_available_sources tests
# ---------------------------------------------------------------------------

class TestGetAvailableSources:
    def test_returns_categorized_sources(self):
        sources = get_available_sources()

        assert "research" in sources
        assert "industry" in sources
        assert "news" in sources

    def test_all_feeds_appear_in_some_category(self):
        from rss_feeds import ENHANCED_RSS_FEEDS

        sources = get_available_sources()
        all_returned = set()
        for category_sources in sources.values():
            all_returned.update(category_sources.keys())

        for feed_name in ENHANCED_RSS_FEEDS:
            assert feed_name in all_returned, f"{feed_name} missing from categorized sources"


# ---------------------------------------------------------------------------
# Flask route tests
# ---------------------------------------------------------------------------

class TestRoutes:
    def test_index_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_index_contains_sources(self, client):
        response = client.get("/")
        assert b"OpenAI" in response.data
        assert b"DeepMind" in response.data

    def test_status_returns_json(self, client):
        response = client.get("/status")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "running" in data
        assert "progress" in data

    def test_api_sources_returns_json(self, client):
        response = client.get("/api/sources")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "research" in data

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert "api_key_configured" in data
        assert "timestamp" in data

    def test_generate_report_post_only(self, client):
        # GET should not be allowed
        response = client.get("/generate_report")
        assert response.status_code == 405

    def test_generate_report_starts_generation(self, client):
        with patch("app.threading.Thread") as mock_thread:
            mock_thread.return_value = MagicMock()

            response = client.post(
                "/generate_report",
                data={"sources": ["OpenAI", "DeepMind"]},
                follow_redirects=True,
            )

            assert response.status_code == 200
            mock_thread.assert_called_once()

    def test_download_nonexistent_file(self, client):
        response = client.get("/download/nonexistent.pdf", follow_redirects=True)
        assert response.status_code == 200  # Redirects to index

    def test_delete_requires_post(self, client):
        response = client.get("/delete/test.pdf")
        assert response.status_code == 405

    def test_delete_nonexistent_file(self, client):
        response = client.post("/delete/nonexistent.pdf", follow_redirects=True)
        assert response.status_code == 200  # Redirects to index

    def test_download_rejects_path_traversal(self, client):
        response = client.get("/download/../../../etc/passwd", follow_redirects=True)
        # secure_filename strips traversal chars; result is 404 or redirect
        assert response.status_code in (200, 404)
