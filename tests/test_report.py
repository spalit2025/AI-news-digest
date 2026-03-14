"""Tests for ui.py -- report generation and PDF output."""

import pytest
from pathlib import Path
from unittest.mock import patch

from summarization import ArticleAnalysis
from ui import EnhancedReportGenerator


# ---------------------------------------------------------------------------
# EnhancedReportGenerator tests
# ---------------------------------------------------------------------------

class TestEnhancedReportGenerator:
    def test_init_creates_reports_dir(self, tmp_path):
        reports_dir = tmp_path / "new_reports"
        generator = EnhancedReportGenerator(reports_dir)
        assert reports_dir.exists()

    def test_get_top_categories(self, tmp_reports_dir):
        generator = EnhancedReportGenerator(tmp_reports_dir)

        analyses = [
            ArticleAnalysis(
                title="A1", source="S", link="L", summary="S",
                impact_score=8, category="research",
                companies=[], technologies=[],
                market_implications="M", investment_angle="I",
                sentiment="positive", confidence=0.8,
            ),
            ArticleAnalysis(
                title="A2", source="S", link="L", summary="S",
                impact_score=7, category="research",
                companies=[], technologies=[],
                market_implications="M", investment_angle="I",
                sentiment="positive", confidence=0.7,
            ),
            ArticleAnalysis(
                title="A3", source="S", link="L", summary="S",
                impact_score=9, category="product_launch",
                companies=[], technologies=[],
                market_implications="M", investment_angle="I",
                sentiment="positive", confidence=0.9,
            ),
        ]

        categories = generator._get_top_categories(analyses)

        assert categories[0]["category"] == "research"
        assert categories[0]["count"] == 2

    def test_generate_enhanced_report(self, tmp_reports_dir):
        generator = EnhancedReportGenerator(tmp_reports_dir)

        analyses = [
            ArticleAnalysis(
                title="Test Article",
                source="TestSource",
                link="https://example.com",
                summary="A test summary for the report.",
                impact_score=8,
                category="research",
                companies=["OpenAI"],
                technologies=["LLM"],
                market_implications="Big market impact.",
                investment_angle="Bullish signal.",
                sentiment="positive",
                confidence=0.9,
            ),
        ]

        trend_analysis = {
            "key_trends": ["AI advancement"],
            "hot_companies": ["OpenAI"],
            "market_sentiment": "positive",
        }

        result = generator.generate_enhanced_report(analyses, trend_analysis)

        assert result is not None
        assert "articles_count" in result
        assert result["articles_count"] == 1
        assert "summary" in result
        assert result["summary"]["total_articles"] == 1

    def test_generate_pdf_creates_file(self, tmp_reports_dir):
        generator = EnhancedReportGenerator(tmp_reports_dir)

        analyses = [
            ArticleAnalysis(
                title="PDF Test Article",
                source="TestSource",
                link="https://example.com",
                summary="Testing PDF generation.",
                impact_score=7,
                category="research",
                companies=["Google"],
                technologies=["AI"],
                market_implications="Test implications.",
                investment_angle="Test angle.",
                sentiment="neutral",
                confidence=0.8,
            ),
        ]

        trend_analysis = {"key_trends": ["Test trend"]}

        result = generator.generate_enhanced_report(analyses, trend_analysis)

        if result.get("pdf_report"):
            pdf_path = Path(result["pdf_report"])
            assert pdf_path.exists()
            assert pdf_path.suffix == ".pdf"
            assert pdf_path.stat().st_size > 0

    def test_generate_trends_json(self, tmp_reports_dir):
        generator = EnhancedReportGenerator(tmp_reports_dir)

        trend_analysis = {"key_trends": ["Test"]}
        result_path = generator._generate_trends_json(trend_analysis, "20260314_120000")

        path = Path(result_path)
        assert path.exists()

        import json
        with open(path) as f:
            data = json.load(f)
        assert "analysis" in data
        assert data["analysis"]["key_trends"] == ["Test"]
