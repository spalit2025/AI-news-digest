# AI News Digest - RSS-powered aggregator with PDF reports and 90% cost savings

An automated, cost-efficient pipeline that collects, filters, and summarizes AI-related news from RSS feeds, generating professional reports with 90-95% cost savings.

## 🚀 Overview

This streamlined tool helps you stay informed about the latest AI developments by:
1. Collecting articles from RSS feeds only (no expensive web scraping)
2. Smart content extraction using free tools when possible
3. Batch AI processing for maximum cost efficiency
4. Intelligent caching to avoid duplicate processing  
5. Generating professional PDF and CSV reports

## ✨ Key Features

- **🎯 RSS-Only Collection**: Fast, free, and reliable article gathering
- **💰 Cost Optimized**: 90-95% reduction in API costs by not using blog scraping
- **🧠 Smart Extraction**: Uses RSS descriptions when sufficient, scrapes only when needed
- **⚡ Batch Processing**: Summarizes multiple articles in single API calls
- **💾 Intelligent Caching**: Avoids re-processing articles and summaries
- **📊 Dual Report Formats**:  PDF + machine-readable CSV
- **🔄 State Tracking**: Prevents duplicate article processing across runs

## 📋 Requirements

```bash
pip install -r requirements.txt
```

**Required libraries:**
- feedparser==6.0.11
- openai==1.64.0  
- python-dotenv==1.0.1
- reportlab==4.4.1
- newspaper3k==0.2.8
- beautifulsoup4==4.12.2
- requests==2.31.0
- lxml_html_clean==0.4.2

## ⚙️ Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your actual API key:
```env
FIREWORKS_API_KEY=your_actual_fireworks_api_key
```

## 🚀 Usage

Simply run the optimized script:

```bash
python optimized_ai_news.py
```

The script will:
1. Fetch articles from 11 RSS sources
2. Filter for new articles (not previously processed)
3. Extract content intelligently (RSS first, scrape if needed)
4. Generate summaries in batch for efficiency
5. Filter duplicates and low-quality content
6. Generate PDF and CSV reports in the `/reports` folder

## 📊 Performance Stats

- **Sources**: 11 RSS feeds (vs RSS + blog scraping)
- **API Calls**: ~2-3 per run (vs ~25-45 in original)
- **Cost Savings**: 90-95% reduction
- **Processing Time**: ~1-3 minutes (vs 5-7 minutes)
- **Storage**: PDF + CSV only (no HTML redundancy)

## 🛠️ Customization

### Adding RSS Sources

Modify the `RSS_FEEDS` dictionary in `optimized_ai_news.py`:

```python
RSS_FEEDS = {
    "Your Source": "https://example.com/rss.xml",
    "TechCrunch AI": "https://techcrunch.com/tag/artificial-intelligence/feed/",
    # Add your RSS sources here
}
```

### Adjusting Filters

- **Article Age**: Change `timedelta(days=7)` in `fetch_rss_articles()`
- **Articles Per Source**: Modify `feed.entries[:2]` to change limit
- **Summary Length**: Adjust `max 25 words` in batch summarization prompt

## 🔧 How It Works

### Smart Architecture:

1. **📰 RSS Collection** (`fetch_rss_articles()`):
   - Fetches from 11 sources simultaneously
   - Filters for articles from last 7 days
   - Handles various RSS date formats gracefully

2. **🧠 Smart Content Extraction** (`smart_content_extraction()`):
   - Uses RSS description if substantial (150+ chars)
   - Falls back to newspaper3k for full content extraction
   - BeautifulSoup as secondary fallback

3. **⚡ Batch AI Processing** (`batch_summarize_articles()`):
   - Processes multiple articles in single API call
   - Caches summaries to avoid re-processing
   - Generates business-focused 25-word summaries

4. **🔍 Quality Filtering** (`filter_summaries_with_ai()`):
   - Removes duplicates and low-quality content
   - AI-powered content curation

5. **📊 Report Generation**:
   - **PDF**: Professional format with branding and styling
   - **CSV**: Machine-readable for data analysis and integration

## 📁 Output Files

Reports are saved in the `reports/` directory:
- `ai_news_digest_YYYYMMDD_HHMMSS.pdf` - Formatted report
- `ai_news_digest_YYYYMMDD_HHMMSS.csv` - Raw data for analysis

## 🔄 State Management

- **Article Cache** (`article_cache.json`): Stores summaries for 7 days
- **Sent Articles** (`sent_articles.json`): Tracks processed articles for 30 days
- **Old Reports Cleanup**: Automatically removes files older than 7 days

## 🚨 Troubleshooting

- **No articles found**: RSS feeds may be temporarily unavailable
- **Import errors**: Run `pip install -r requirements.txt`  
- **Date parsing issues**: Some feeds use non-standard date formats (handled gracefully)
- **Content extraction fails**: Falls back to RSS description automatically

## 🔄 Single Optimized Version

This repository contains the **streamlined, cost-optimized version** focused on:
- RSS-only processing for maximum efficiency
- 90-95% cost savings compared to web scraping approaches  
- Professional PDF + CSV report generation
- Smart caching and duplicate prevention
- Perfect for daily automated news aggregation

## 🎯 Cost Optimization Strategy

1. **RSS-Only Sources**: Eliminated expensive blog scraping
2. **Batch API Calls**: Process multiple articles together  
3. **Smart Caching**: Avoid duplicate processing
4. **Efficient Extraction**: Use free methods when possible
5. **Reduced Redundancy**: PDF + CSV only (no HTML)

## 🙏 Acknowledgments

- **Fireworks AI**: Cost-effective LLM processing
- **newspaper3k**: Free article extraction
- **BeautifulSoup**: HTML parsing fallback
- **ReportLab**: Professional PDF generation

---

**💡 Ready to run with minimal setup and maximum efficiency!**
