# AI News Digest - RSS-powered aggregator with 90% cost savings

An automated tool that collects AI news from RSS feeds and generates daily reports in PDF and CSV formats.

## What it does

- Fetches articles from 11 AI industry RSS feeds
- Extracts and summarizes content using AI
- Filters out duplicates and low-quality articles
- Generates professional reports saved locally
- Tracks processed articles to avoid duplicates

## Features

- **🎯 RSS-Only Collection**: Fast, free, and reliable article gathering
- **💰 Cost Optimized**: 90-95% reduction in API costs by not using blog scraping
- **🧠 Smart Extraction**: Uses RSS descriptions when sufficient, scrapes only when needed
- **⚡ Batch Processing**: Summarizes multiple articles in single API calls
- **💾 Intelligent Caching**: Avoids re-processing articles and summaries
- **📊 Dual Report Formats**: PDF + machine-readable CSV
- **🔄 State Tracking**: Prevents duplicate article processing across runs

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install feedparser openai python-dotenv reportlab newspaper3k beautifulsoup4 requests
```

3. Create `.env` file:
```env
FIREWORKS_API_KEY=your_fireworks_api_key
```

4. Run the script:
```bash
python optimized_ai_news.py
```

## Configuration

The script uses these RSS sources by default:
- Nvidia, TechCrunch AI, MIT Tech Review
- ArXiv AI, Hugging Face, Google AI  
- OpenAI, Meta AI, Anthropic
- The Verge AI, Ars Technica AI

To add sources, edit the `RSS_FEEDS` dictionary in the script.

## Output

Reports are saved in the `reports/` folder:
- **PDF**: Formatted report with summaries and links
- **CSV**: Raw data for further analysis

## How it works

1. Fetches recent articles from RSS feeds
2. Extracts content using newspaper3k or BeautifulSoup
3. Generates summaries using Fireworks AI
4. Filters duplicates with AI
5. Creates PDF and CSV reports
6. Caches results to avoid reprocessing

## State management

- `article_cache.json` - Stores summaries (7 days)
- `sent_articles.json` - Tracks processed articles (30 days)

## Requirements

- Python 3.7+
- Fireworks AI API key
- feedparser==6.0.11
- openai==1.64.0
- python-dotenv==1.0.1
- reportlab==4.4.1
- newspaper3k==0.2.8
- beautifulsoup4==4.12.2
- requests==2.31.0

---

A simple, efficient solution for staying updated on AI industry news.