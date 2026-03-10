# AI News Digest

Staying current on AI research and industry news means scanning dozens of
sources daily -- blogs, research labs, company announcements -- and figuring
out what actually matters. Most of it is noise.

AI News Digest aggregates 19+ curated AI/ML sources, uses LLM-powered analysis
to score each article by impact, and generates structured digest reports with
executive summaries and trend analysis. One click, one report, every morning.

## Why I built this

I was spending 30+ minutes daily scanning AI news across scattered sources.
I wanted to explore:

1. **Can AI reliably score "what matters" in a news feed?** Multi-dimensional
   impact scoring (1-10) with automatic categorization -- turning a firehose
   of articles into a ranked, actionable digest.
2. **What does a useful AI-generated report look like?** Not just summaries,
   but cross-article trend analysis, market implications, and executive
   overviews that surface patterns humans miss when reading one article at a time.
3. **How do you build a reliable daily pipeline?** RSS feed health monitoring,
   intelligent caching to avoid reprocessing, rate limiting to stay within
   API budgets, and duplicate detection across sources.

## Demo

<!-- TODO: Add screenshot of the web interface showing a generated report -->

## Quick start

```bash
# Clone and install
git clone https://github.com/spalit2025/AI-news-digest.git
cd AI-news-digest
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your FIREWORKS_API_KEY

# Launch
python app.py
# Open http://localhost:8080
```

Click "Generate Report" and watch real-time progress as it fetches, analyzes,
and compiles the digest.

## How it works

```
19+ RSS Feeds (DeepMind, OpenAI, Anthropic, HuggingFace, NVIDIA, Google AI...)
    |
    | Fetch + deduplicate + cache
    |
Enhanced RSS Engine
    |
    ├── Feed health monitoring (track reliability per source)
    └── Duplicate detection (skip already-processed articles)
    |
AI Analysis (Fireworks API)
    |
    ├── Impact scoring (1-10, multi-dimensional)
    ├── Categorization (research, product, funding, policy, etc.)
    ├── Market analysis (business implications, investment signals)
    └── Trend synthesis (cross-article patterns)
    |
Report Generator
    |
    ├── Web UI (real-time progress, interactive dashboard)
    └── PDF export (executive summary, full analysis, trend map)
```

## Architecture

- `app.py` -- Flask web application, routes, report management
- `enhanced_rss_feeds.py` -- RSS feed management with health monitoring
- `enhanced_summarization.py` -- LLM-powered analysis, scoring, categorization
- `enhanced_ui.py` -- Report generation and formatting
- `templates/index.html` -- Web interface with real-time progress tracking
- `static/` -- CSS and JavaScript for the frontend

## Key design decisions

- **Impact scoring over chronological listing:** Raw feeds are noisy. A scored,
  ranked digest surfaces the 5 articles that matter from 50+ that don't.

- **Fireworks API over local LLMs:** Unlike DocuMatch (where privacy requires
  local processing), news articles are public. Fireworks gives better analysis
  quality at reasonable cost for a daily digest use case.

- **Feed health monitoring:** RSS feeds break silently. Tracking reliability
  per source means the system degrades gracefully when a feed goes down
  instead of producing incomplete reports.

- **Aggressive caching and deduplication:** The same story appears on multiple
  blogs. Duplicate detection across sources prevents the digest from being
  dominated by one viral announcement.

## Sources

The system monitors 19+ AI/ML sources including DeepMind Research, OpenAI Blog,
Anthropic News, Hugging Face Blog, NVIDIA AI Blog, Google AI Blog, and Meta AI
Research. Sources are configurable in `enhanced_rss_feeds.py`.

## Requirements

- Python 3.8+
- [Fireworks AI API key](https://fireworks.ai/) (for LLM analysis)

## License

MIT
