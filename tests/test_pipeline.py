"""Tests for the end-to-end pipeline in app.py."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app import run_enhanced_pipeline, report_manager


# ---------------------------------------------------------------------------
# Pipeline integration tests
# ---------------------------------------------------------------------------

class TestPipeline:
    @patch("app.StateTracker")
    @patch("app.extract_article_content")
    @patch("app.fetch_rss_articles")
    @patch("app.EnhancedReportGenerator")
    @patch("app.EnhancedSummarizer")
    def test_pipeline_happy_path(
        self, MockSummarizer, MockReportGen, mock_fetch, mock_extract, MockTracker
    ):
        # Setup mocks
        mock_fetch.return_value = [
            {"title": "Test", "link": "https://example.com", "source": "Test", "description": "Desc"},
        ]
        mock_tracker = MockTracker.return_value
        mock_tracker.filter_new_articles.return_value = mock_fetch.return_value

        mock_extract.return_value = "Article content here"

        mock_summarizer = MockSummarizer.return_value
        mock_analysis = MagicMock()
        mock_analysis.title = "Test"
        mock_summarizer.batch_analyze_articles.return_value = [mock_analysis]
        mock_summarizer.generate_trend_analysis.return_value = {"key_trends": ["AI"]}

        mock_report_gen = MockReportGen.return_value
        mock_report_gen.generate_enhanced_report.return_value = {
            "pdf_report": "/tmp/test.pdf",
            "articles_count": 1,
        }

        result = run_enhanced_pipeline(selected_sources=["OpenAI"])

        assert result is not None
        assert result["pdf_report"] == "/tmp/test.pdf"
        mock_tracker.mark_articles_sent.assert_called_once()

    @patch("app.fetch_rss_articles")
    def test_pipeline_no_articles(self, mock_fetch):
        mock_fetch.return_value = []

        result = run_enhanced_pipeline()

        assert result is None

    def test_pipeline_no_api_key(self):
        with patch.dict("os.environ", {"FIREWORKS_API_KEY": ""}):
            with pytest.raises(Exception, match="FIREWORKS_API_KEY"):
                run_enhanced_pipeline()

    def test_pipeline_placeholder_api_key(self):
        with patch.dict("os.environ", {"FIREWORKS_API_KEY": "your_fireworks_api_key_here"}):
            with pytest.raises(Exception, match="FIREWORKS_API_KEY"):
                run_enhanced_pipeline()

    @patch("app.StateTracker")
    @patch("app.fetch_rss_articles")
    def test_pipeline_all_articles_already_processed(self, mock_fetch, MockTracker):
        mock_fetch.return_value = [
            {"title": "Old", "link": "https://example.com/old", "source": "Test"},
        ]
        mock_tracker = MockTracker.return_value
        mock_tracker.filter_new_articles.return_value = []  # All filtered out

        result = run_enhanced_pipeline()

        assert result is None

    @patch("app.StateTracker")
    @patch("app.extract_article_content")
    @patch("app.fetch_rss_articles")
    def test_pipeline_no_extractable_content(self, mock_fetch, mock_extract, MockTracker):
        mock_fetch.return_value = [
            {"title": "Test", "link": "https://example.com", "source": "Test"},
        ]
        mock_tracker = MockTracker.return_value
        mock_tracker.filter_new_articles.return_value = mock_fetch.return_value

        mock_extract.return_value = None  # No content extracted

        result = run_enhanced_pipeline()

        assert result is None

    def test_pipeline_invalid_sources(self):
        with pytest.raises(Exception, match="No valid sources"):
            run_enhanced_pipeline(selected_sources=["NonexistentSource123"])
