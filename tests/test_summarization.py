"""Tests for summarization.py -- LLM analysis, JSON parsing, and trend synthesis."""

import json
import pytest
from unittest.mock import patch, MagicMock

from summarization import EnhancedSummarizer, ArticleAnalysis, ArticleFilter


# ---------------------------------------------------------------------------
# _parse_json_response tests
# ---------------------------------------------------------------------------

class TestParseJsonResponse:
    def setup_method(self):
        self.summarizer = EnhancedSummarizer("test-key")

    def test_parse_valid_json(self):
        raw = '{"key": "value", "number": 42}'
        result = self.summarizer._parse_json_response(raw)
        assert result == {"key": "value", "number": 42}

    def test_parse_json_in_code_block(self):
        raw = 'Here is the analysis:\n```json\n{"key": "value"}\n```\nDone.'
        result = self.summarizer._parse_json_response(raw)
        assert result == {"key": "value"}

    def test_parse_json_in_generic_code_block(self):
        raw = '```\n{"key": "value"}\n```'
        result = self.summarizer._parse_json_response(raw)
        assert result == {"key": "value"}

    def test_parse_json_embedded_in_text(self):
        raw = 'The analysis result is {"key": "value"} based on the article.'
        result = self.summarizer._parse_json_response(raw)
        assert result == {"key": "value"}

    def test_parse_no_json_returns_none(self):
        raw = "This response has no JSON at all."
        result = self.summarizer._parse_json_response(raw)
        assert result is None

    def test_parse_empty_string(self):
        result = self.summarizer._parse_json_response("")
        assert result is None

    def test_parse_whitespace_around_json(self):
        raw = '  \n  {"key": "value"}  \n  '
        result = self.summarizer._parse_json_response(raw)
        assert result == {"key": "value"}


# ---------------------------------------------------------------------------
# analyze_article tests
# ---------------------------------------------------------------------------

class TestAnalyzeArticle:
    def setup_method(self):
        self.summarizer = EnhancedSummarizer("test-key")

    @patch.object(EnhancedSummarizer, "_rate_limited_api_call")
    def test_analyze_returns_article_analysis(self, mock_api, sample_analysis_json):
        mock_api.return_value = sample_analysis_json

        article = {
            "title": "Test Article",
            "source": "TestSource",
            "link": "https://example.com",
            "content": "Some content about AI.",
        }

        result = self.summarizer.analyze_article(article)

        assert isinstance(result, ArticleAnalysis)
        assert result.title == "Test Article"
        assert result.impact_score == 9
        assert result.category == "product_launch"
        assert "OpenAI" in result.companies

    @patch.object(EnhancedSummarizer, "_rate_limited_api_call")
    def test_analyze_fallback_on_api_failure(self, mock_api):
        mock_api.return_value = None

        article = {
            "title": "Test Article",
            "source": "TestSource",
            "link": "https://example.com",
            "content": "Content",
        }

        result = self.summarizer.analyze_article(article)

        assert isinstance(result, ArticleAnalysis)
        assert result.impact_score == 5  # Fallback default
        assert result.confidence == 0.3  # Low confidence fallback

    @patch.object(EnhancedSummarizer, "_rate_limited_api_call")
    def test_analyze_fallback_on_garbage_response(self, mock_api):
        mock_api.return_value = "This is not JSON at all! Just random text."

        article = {
            "title": "Test",
            "source": "Test",
            "link": "https://example.com",
            "content": "Content",
        }

        result = self.summarizer.analyze_article(article)

        assert isinstance(result, ArticleAnalysis)
        assert result.confidence == 0.3  # Fallback

    @patch.object(EnhancedSummarizer, "_rate_limited_api_call")
    def test_analyze_clamps_impact_score(self, mock_api):
        mock_api.return_value = json.dumps({
            "summary": "Test",
            "impact_score": 15,  # Over max
            "category": "research",
            "companies": [],
            "technologies": [],
            "market_implications": "Test",
            "investment_angle": "Test",
            "sentiment": "positive",
            "confidence": 0.8,
        })

        article = {"title": "T", "source": "S", "link": "https://x.com", "content": "C"}
        result = self.summarizer.analyze_article(article)

        assert result.impact_score == 10  # Clamped to max

    @patch.object(EnhancedSummarizer, "_rate_limited_api_call")
    def test_analyze_handles_none_content(self, mock_api, sample_analysis_json):
        mock_api.return_value = sample_analysis_json

        article = {
            "title": "Test",
            "source": "Test",
            "link": "https://example.com",
            "content": None,  # Explicitly None
        }

        result = self.summarizer.analyze_article(article)

        # Should not raise TypeError, should produce valid analysis
        assert isinstance(result, ArticleAnalysis)


# ---------------------------------------------------------------------------
# batch_analyze_articles tests
# ---------------------------------------------------------------------------

class TestBatchAnalyze:
    @patch.object(EnhancedSummarizer, "_rate_limited_api_call")
    def test_batch_processes_all_articles(self, mock_api, sample_analysis_json, sample_articles_with_content):
        mock_api.return_value = sample_analysis_json

        summarizer = EnhancedSummarizer("test-key")
        results = summarizer.batch_analyze_articles(sample_articles_with_content)

        assert len(results) == 3
        assert all(isinstance(r, ArticleAnalysis) for r in results)


# ---------------------------------------------------------------------------
# generate_trend_analysis tests
# ---------------------------------------------------------------------------

class TestTrendAnalysis:
    def setup_method(self):
        self.summarizer = EnhancedSummarizer("test-key")

    @patch.object(EnhancedSummarizer, "_rate_limited_api_call")
    def test_trend_analysis_returns_dict(self, mock_api, sample_trend_json):
        mock_api.return_value = sample_trend_json

        analyses = [
            ArticleAnalysis(
                title="Test", source="Test", link="https://x.com",
                summary="Test summary", impact_score=8, category="research",
                companies=["OpenAI"], technologies=["LLM"],
                market_implications="Big", investment_angle="Bullish",
                sentiment="positive", confidence=0.9,
            )
        ]

        result = self.summarizer.generate_trend_analysis(analyses)

        assert "key_trends" in result
        assert "hot_companies" in result

    @patch.object(EnhancedSummarizer, "_rate_limited_api_call")
    def test_trend_analysis_fallback_on_failure(self, mock_api):
        mock_api.return_value = None

        analyses = [
            ArticleAnalysis(
                title="Test", source="Test", link="https://x.com",
                summary="Test", impact_score=7, category="research",
                companies=["Google"], technologies=["AI"],
                market_implications="Test", investment_angle="Test",
                sentiment="neutral", confidence=0.8,
            )
        ]

        result = self.summarizer.generate_trend_analysis(analyses)

        assert "key_trends" in result  # Fallback still returns trends

    def test_trend_analysis_empty_list(self):
        result = self.summarizer.generate_trend_analysis([])
        assert "error" in result


# ---------------------------------------------------------------------------
# ArticleFilter tests
# ---------------------------------------------------------------------------

class TestArticleFilter:
    def test_relevance_score_breakthrough_boosted(self):
        analysis = ArticleAnalysis(
            title="T", source="S", link="L", summary="S",
            impact_score=8, category="breakthrough",
            companies=[], technologies=[],
            market_implications="M", investment_angle="I",
            sentiment="positive", confidence=0.9,
        )

        score = ArticleFilter.relevance_score(analysis)

        # breakthrough gets 2.0 boost
        assert score > 5.0

    def test_filter_by_quality_removes_low_confidence(self):
        good = ArticleAnalysis(
            title="Good", source="S", link="L", summary="S",
            impact_score=7, category="research",
            companies=[], technologies=[],
            market_implications="M", investment_angle="I",
            sentiment="positive", confidence=0.8,
        )
        bad = ArticleAnalysis(
            title="Bad", source="S", link="L", summary="S",
            impact_score=2, category="general",
            companies=[], technologies=[],
            market_implications="M", investment_angle="I",
            sentiment="neutral", confidence=0.2,
        )

        filt = ArticleFilter()
        result = filt.filter_by_quality([good, bad])

        assert len(result) == 1
        assert result[0].title == "Good"
