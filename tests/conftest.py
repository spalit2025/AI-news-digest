"""Shared fixtures for the AI News Digest test suite."""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Set test environment before importing app modules
os.environ["FIREWORKS_API_KEY"] = "test-api-key-for-testing"
os.environ["FLASK_SECRET_KEY"] = "test-secret-key"


@pytest.fixture
def app():
    """Create a Flask test app."""
    from app import app as flask_app

    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    return flask_app


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    return app.test_client()


@pytest.fixture
def sample_articles():
    """Sample article dicts as returned by fetch_rss_articles."""
    return [
        {
            "title": "OpenAI Announces GPT-5",
            "link": "https://openai.com/blog/gpt-5",
            "source": "OpenAI",
            "published": "2026-03-14",
            "description": "OpenAI today announced GPT-5 with breakthrough capabilities.",
        },
        {
            "title": "Google DeepMind Achieves New Milestone",
            "link": "https://deepmind.com/blog/new-milestone",
            "source": "DeepMind",
            "published": "2026-03-14",
            "description": "DeepMind researchers demonstrate improved reasoning.",
        },
        {
            "title": "Anthropic Releases Claude 5",
            "link": "https://anthropic.com/news/claude-5",
            "source": "Anthropic",
            "published": "2026-03-14",
            "description": "Anthropic launches Claude 5 with enhanced safety features.",
        },
    ]


@pytest.fixture
def sample_articles_with_content(sample_articles):
    """Sample articles with extracted content."""
    for article in sample_articles:
        article["content"] = article["description"] * 5  # Pad content
    return sample_articles


@pytest.fixture
def sample_analysis_json():
    """Sample JSON response from the LLM analysis."""
    return json.dumps({
        "summary": "OpenAI announced GPT-5 with breakthrough capabilities in reasoning.",
        "impact_score": 9,
        "category": "product_launch",
        "companies": ["OpenAI"],
        "technologies": ["GPT-5", "LLM"],
        "market_implications": "Major competitive shift in the AI industry.",
        "investment_angle": "Bullish signal for AI infrastructure companies.",
        "sentiment": "positive",
        "confidence": 0.9,
    })


@pytest.fixture
def sample_trend_json():
    """Sample JSON response from the trend analysis."""
    return json.dumps({
        "key_trends": ["AI model advancement", "Enterprise AI adoption"],
        "hot_companies": ["OpenAI", "Google", "Anthropic"],
        "emerging_technologies": ["LLM", "AI Agents"],
        "market_sentiment": "positive",
        "investment_themes": ["AI infrastructure", "Enterprise AI"],
        "notable_insights": ["Rapid pace of model releases"],
    })


@pytest.fixture
def mock_openai_response(sample_analysis_json):
    """Mock OpenAI API response object."""
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = sample_analysis_json
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    return mock_response


@pytest.fixture
def tmp_state_file(tmp_path):
    """Temporary state file for StateTracker tests."""
    return str(tmp_path / "test_sent_articles.json")


@pytest.fixture
def tmp_reports_dir(tmp_path):
    """Temporary reports directory."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    return reports_dir
