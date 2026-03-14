"""Tests for rss_feeds.py -- feed management, fetching, extraction, and state tracking."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from rss_feeds import (
    ENHANCED_RSS_FEEDS,
    FEED_CATEGORIES,
    FEED_QUALITY_METRICS,
    get_prioritized_feeds,
    fetch_rss_articles,
    extract_article_content,
    RSSFeedValidator,
    StateTracker,
)


# ---------------------------------------------------------------------------
# Feed configuration tests
# ---------------------------------------------------------------------------

class TestFeedConfiguration:
    def test_enhanced_feeds_not_empty(self):
        assert len(ENHANCED_RSS_FEEDS) > 0

    def test_all_feed_urls_are_strings(self):
        for name, url in ENHANCED_RSS_FEEDS.items():
            assert isinstance(url, str), f"{name} has non-string URL"
            assert url.startswith("http"), f"{name} URL doesn't start with http"

    def test_feed_categories_reference_valid_sources(self):
        all_sources = set(ENHANCED_RSS_FEEDS.keys())
        for category, names in FEED_CATEGORIES.items():
            for name in names:
                assert name in all_sources, (
                    f"Category '{category}' references unknown source '{name}'"
                )

    def test_get_prioritized_feeds_returns_correct_count(self):
        feeds = get_prioritized_feeds(5)
        assert len(feeds) == 5

    def test_get_prioritized_feeds_returns_highest_scored_first(self):
        feeds = get_prioritized_feeds(3)
        feed_names = list(feeds.keys())
        # The highest-scored feeds (DeepMind=10, OpenAI=10, Anthropic=9)
        # should appear in the top 3
        top_names = set(feed_names)
        assert "DeepMind" in top_names or "OpenAI" in top_names

    def test_get_prioritized_feeds_max_exceeds_total(self):
        feeds = get_prioritized_feeds(100)
        assert len(feeds) == len(ENHANCED_RSS_FEEDS)


# ---------------------------------------------------------------------------
# fetch_rss_articles tests
# ---------------------------------------------------------------------------

class TestFetchRssArticles:
    @patch("rss_feeds.requests.get")
    @patch("rss_feeds.feedparser.parse")
    def test_fetch_returns_articles(self, mock_parse, mock_get):
        mock_get.return_value = MagicMock(content=b"<rss></rss>")
        mock_parse.return_value = MagicMock(
            entries=[
                MagicMock(
                    **{
                        "get.side_effect": lambda k, d="": {
                            "title": "Test Article",
                            "link": "https://example.com/article",
                            "published": "2026-03-14",
                            "summary": "A test article.",
                        }.get(k, d)
                    }
                )
            ]
        )

        articles = fetch_rss_articles({"TestSource": "https://example.com/feed"})

        assert len(articles) == 1
        assert articles[0]["title"] == "Test Article"
        assert articles[0]["source"] == "TestSource"

    @patch("rss_feeds.requests.get")
    def test_fetch_handles_timeout(self, mock_get):
        mock_get.side_effect = Exception("Connection timeout")

        articles = fetch_rss_articles({"BadSource": "https://broken.example.com/feed"})

        assert articles == []

    @patch("rss_feeds.requests.get")
    @patch("rss_feeds.feedparser.parse")
    def test_fetch_handles_empty_feed(self, mock_parse, mock_get):
        mock_get.return_value = MagicMock(content=b"<rss></rss>")
        mock_parse.return_value = MagicMock(entries=[])

        articles = fetch_rss_articles({"EmptySource": "https://empty.example.com/feed"})

        assert articles == []

    def test_fetch_empty_feeds_dict(self):
        articles = fetch_rss_articles({})
        assert articles == []


# ---------------------------------------------------------------------------
# extract_article_content tests
# ---------------------------------------------------------------------------

class TestExtractArticleContent:
    @patch("rss_feeds.requests.get")
    def test_extract_returns_content(self, mock_get):
        html = "<html><body><article><p>" + "Test content. " * 50 + "</p></article></body></html>"
        mock_get.return_value = MagicMock(status_code=200, text=html)

        content = extract_article_content({"link": "https://example.com/article", "description": "fallback"})

        assert content is not None
        assert "Test content" in content

    @patch("rss_feeds.requests.get")
    def test_extract_falls_back_on_http_error(self, mock_get):
        mock_get.return_value = MagicMock(status_code=404)

        content = extract_article_content({"link": "https://example.com/404", "description": "fallback text"})

        assert content == "fallback text"

    @patch("rss_feeds.requests.get")
    def test_extract_falls_back_on_exception(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        content = extract_article_content({"link": "https://example.com/error", "description": "fallback"})

        assert content == "fallback"

    def test_extract_no_link_returns_description(self):
        content = extract_article_content({"description": "no link fallback"})

        assert content == "no link fallback"

    def test_extract_empty_article(self):
        content = extract_article_content({})
        assert content == ""

    @patch("rss_feeds.requests.get")
    def test_extract_limits_content_length(self, mock_get):
        html = "<html><body><p>" + "x" * 10000 + "</p></body></html>"
        mock_get.return_value = MagicMock(status_code=200, text=html)

        content = extract_article_content({"link": "https://example.com/long"})

        assert len(content) <= 5000


# ---------------------------------------------------------------------------
# StateTracker tests
# ---------------------------------------------------------------------------

class TestStateTracker:
    def test_filter_new_articles(self, tmp_state_file, sample_articles):
        tracker = StateTracker(state_file=tmp_state_file)

        new = tracker.filter_new_articles(sample_articles)

        assert len(new) == 3  # All articles are new

    def test_mark_and_filter(self, tmp_state_file, sample_articles):
        tracker = StateTracker(state_file=tmp_state_file)

        # Mark first article as sent
        tracker.mark_articles_sent(["https://openai.com/blog/gpt-5"])

        new = tracker.filter_new_articles(sample_articles)

        assert len(new) == 2
        assert all(a["link"] != "https://openai.com/blog/gpt-5" for a in new)

    def test_state_persists_across_instances(self, tmp_state_file, sample_articles):
        tracker1 = StateTracker(state_file=tmp_state_file)
        tracker1.mark_articles_sent(["https://openai.com/blog/gpt-5"])

        # New instance should load saved state
        tracker2 = StateTracker(state_file=tmp_state_file)
        new = tracker2.filter_new_articles(sample_articles)

        assert len(new) == 2

    def test_handles_missing_state_file(self, tmp_path):
        tracker = StateTracker(state_file=str(tmp_path / "nonexistent.json"))
        assert tracker.filter_new_articles([{"link": "https://example.com"}]) == [{"link": "https://example.com"}]

    def test_handles_corrupt_state_file(self, tmp_path):
        state_file = tmp_path / "corrupt.json"
        state_file.write_text("not valid json{{{")

        tracker = StateTracker(state_file=str(state_file))

        # Should treat all as new (empty state)
        articles = [{"link": "https://example.com"}]
        assert len(tracker.filter_new_articles(articles)) == 1

    def test_filter_articles_without_link(self, tmp_state_file):
        tracker = StateTracker(state_file=tmp_state_file)
        articles = [{"title": "No link article"}]

        new = tracker.filter_new_articles(articles)

        assert len(new) == 1  # Article without link is always "new"


# ---------------------------------------------------------------------------
# RSSFeedValidator tests
# ---------------------------------------------------------------------------

class TestRSSFeedValidator:
    @patch("rss_feeds.requests.get")
    @patch("rss_feeds.requests.head")
    def test_validate_valid_feed(self, mock_head, mock_get):
        mock_head.return_value = MagicMock(status_code=200)
        mock_get.return_value = MagicMock(content=b"<rss></rss>")

        with patch("rss_feeds.feedparser.parse") as mock_parse:
            mock_parse.return_value = MagicMock(entries=[MagicMock()])

            validator = RSSFeedValidator()
            is_valid, message, redirect_url = validator.validate_feed("https://example.com/feed")

            assert is_valid is True
            assert redirect_url is None

    @patch("rss_feeds.requests.head")
    def test_validate_timeout(self, mock_head):
        mock_head.side_effect = Exception("Timeout")

        validator = RSSFeedValidator()
        is_valid, message, redirect_url = validator.validate_feed("https://broken.example.com/feed")

        assert is_valid is False
        assert "Error" in message
