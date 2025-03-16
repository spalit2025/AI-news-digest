# AI News RSS Aggregator

An automated pipeline that collects, filters, and summarizes AI-related news and research from various sources, delivering a curated digest via email.

## Overview

This tool helps you stay informed about the latest developments in AI by:
1. Collecting articles from RSS feeds and blog sources
2. Filtering for only the most recent articles (past week)
3. Extracting and summarizing content
4. Removing duplicates and low-quality articles
5. Delivering a digest via email with a CSV attachment

## Features

- **Multi-source collection**: Aggregates content from RSS feeds and blogs
- **Intelligent filtering**: Uses LLM-based filtering to eliminate duplicates and low-quality content
- **Concise summaries**: Generates business-relevant, single-line summaries of each article
- **Email delivery**: Sends a formatted HTML digest with all articles
- **CSV download**: Includes a CSV attachment with all article data for reference or analysis

## Requirements

- Python 3.8+
- Required libraries:
  - feedparser
  - openai (or similar client)
  - crawl4ai (for web crawling)
  - pydantic

## Configuration

Set the following environment variables before running:

```
FIREWORKS_API_KEY=your_fireworks_api_key
SMTP_SERVER=your_smtp_server
SMTP_PORT=your_smtp_port
EMAIL_SENDER=your_sender_email
EMAIL_PASSWORD=your_email_password
EMAIL_RECIPIENT=recipient1@example.com; recipient2@example.com
```

## Usage

Simply run the script:

```
python rss_feed_v3.py
```

The script will:
1. Fetch articles from the configured RSS feeds and blogs
2. Process and filter them
3. Send an email digest to the configured recipients

## Customization

### Adding RSS Sources

Modify the `RSS_FEEDS` dictionary to add or remove sources:

```python
RSS_FEEDS = {  
    "Wired AI": "https://www.wired.com/feed/tag/ai/latest/rss",
    "TechCrunch AI": "https://techcrunch.com/tag/artificial-intelligence/feed/",
    # Add your sources here
}
```

### Adding Blog Sources

Modify the `BLOG_URLS` dictionary to add or remove blog sources:

```python
BLOG_URLS = {
    "Stability AI news": "https://stability.ai/news",
    "Stability AI research": "https://stability.ai/research",
    # Add your blog sources here
}
```

## How It Works

1. **Article Collection**:
   - `fetch_rss_articles()`: Collects articles from RSS feeds published in the last 24 hours
   - `fetch_blog_articles()`: Uses AI to extract recent articles from blog websites

2. **Content Processing**:
   - `scrape_article_content()`: Extracts the full text of each article
   - `summarize_article()`: Creates a concise, business-focused summary

3. **Quality Control**:
   - `filter_summaries_with_ai()`: Removes duplicates and low-quality content using an LLM

4. **Delivery**:
   - `create_email_content()`: Formats the article summaries into HTML
   - `create_articles_csv()`: Creates a CSV with all article data
   - `send_email()`: Delivers the digest to recipients

## Troubleshooting

- **No articles being returned**: Check that your RSS feeds and blog URLs are valid and contain recent content
- **Email delivery issues**: Verify your SMTP settings and email credentials
- **Date parsing errors**: The code includes robust date parsing, but some feeds may use unusual formats

## Acknowledgments

- Uses OpenAI API / Fireworks.ai API for LLM processing
- Uses crawl4ai for web crawling capabilities

## Feel free to fork this repo, modify the sources and improve the functionality. Happy coding!
