# Optimized AI News Aggregation Script
# Author: Streamlined version - Maximum cost reduction via RSS-only approach
# Estimated 90-95% reduction in API costs

import feedparser
import csv
import os
import json
import hashlib
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

# Free content extraction libraries
try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
    print("✅ newspaper3k available for content extraction")
except ImportError:
    NEWSPAPER_AVAILABLE = False
    print("Warning: newspaper3k not installed. Run: pip install newspaper3k")

# PDF generation library
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: reportlab not installed. Run: pip install reportlab")

load_dotenv()

# Configuration - All RSS Feeds (FREE & FAST) - No AI scraping needed!
RSS_FEEDS = {
    "Nvidia": "https://blogs.nvidia.com/blog/category/ai/feed/",
    "TechCrunch AI": "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "MIT Tech Review": "https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml",
    "ArXiv AI": "http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=2",
    "Hugging Face Blog": "https://huggingface.co/blog/feed.xml",
    "Google AI": "https://ai.googleblog.com/feeds/posts/default",
    "OpenAI": "https://openai.com/news/rss.xml",
    "Meta AI": "https://research.fb.com/feed/",
    "Anthropic": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic.xml",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "Ars Technica AI": "https://feeds.arstechnica.com/arstechnica/ai"
}

# API Configuration
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")

# Report Configuration
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)  # Create reports directory if it doesn't exist


class ArticleCache:
    """Cache system to avoid re-processing articles"""
    
    def __init__(self, cache_file="article_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache = self.load_cache()
    
    def load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def get_cache_key(self, url):
        return hashlib.md5(url.encode()).hexdigest()
    
    def get_summary(self, url):
        key = self.get_cache_key(url)
        cached_item = self.cache.get(key)
        if cached_item:
            # Check if cache is not too old (7 days)
            cached_date = datetime.fromisoformat(cached_item.get('cached_date', '2020-01-01'))
            if datetime.now() - cached_date < timedelta(days=7):
                return cached_item['summary']
        return None
    
    def set_summary(self, url, summary):
        key = self.get_cache_key(url)
        self.cache[key] = {
            'summary': summary,
            'cached_date': datetime.now().isoformat()
        }
        self.save_cache()


class StateTracker:
    """Track sent articles to avoid duplicates"""
    
    def __init__(self, state_file="sent_articles.json"):
        self.state_file = Path(state_file)
        self.sent_urls = self.load_sent_articles()
    
    def load_sent_articles(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    # Clean old entries (older than 30 days)
                    cutoff = datetime.now() - timedelta(days=30)
                    return {url: sent_date for url, sent_date in data.items() 
                           if datetime.fromisoformat(sent_date) > cutoff}
            except:
                return {}
        return {}
    
    def is_article_sent(self, url):
        return url in self.sent_urls
    
    def mark_articles_sent(self, urls):
        current_time = datetime.now().isoformat()
        for url in urls:
            self.sent_urls[url] = current_time
        self.save_state()
    
    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.sent_urls, f, indent=2)
    
    def filter_new_articles(self, articles):
        """Remove articles that were already sent"""
        new_articles = [article for article in articles 
                       if not self.is_article_sent(article['link'])]
        print(f"Filtered: {len(articles)} total → {len(new_articles)} new articles")
        return new_articles


def fetch_rss_articles():
    """Fetch articles from RSS feeds (unchanged, already efficient)"""
    articles = []
    current_time = datetime.now()
    cutoff_time = current_time - timedelta(days=7)

    for source, url in RSS_FEEDS.items():
        print(f"Fetching RSS feed: {source}")
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                print(f"Warning: No entries found in {url}")
                continue
        except Exception as e:
            print(f"Error fetching RSS feed {url}: {e}")
            continue
            
        for entry in feed.entries[:2]:  # Limit to 2 most recent
            title = entry.title
            link = entry.link
            description = entry.get('description', entry.get('summary', ''))
            description = description.replace('<p>', '').replace('</p>', '')
            
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                except (TypeError, ValueError, OverflowError):
                    # Try updated_parsed as fallback
                    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        try:
                            published_time = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                        except (TypeError, ValueError, OverflowError):
                            print(f"Warning: Invalid date information for {title}. Skipping.")
                            continue
                    else:
                        print(f"Warning: No valid date information for {title}. Skipping.")
                        continue
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                try:
                    published_time = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                except (TypeError, ValueError, OverflowError):
                    print(f"Warning: Invalid date information for {title}. Skipping.")
                    continue
            else:
                print(f"Warning: No date information for {title}. Skipping.")
                continue
                
            if published_time >= cutoff_time:
                print(f"Found recent article: {link}")
                articles.append({
                    "source": source, 
                    "title": title, 
                    "link": link,
                    "description": description
                })
            else:
                print(f"Skipping older article: {link}")
    
    return articles


def extract_content_free(url):
    """Free content extraction using newspaper3k and BeautifulSoup"""
    
    # Try newspaper3k first (most reliable)
    if NEWSPAPER_AVAILABLE:
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            if article.text and len(article.text) > 200:
                print(f"  ✅ Extracted content via newspaper3k")
                return article.text
        except Exception as e:
            print(f"  Newspaper3k failed: {e}")
    
    # Fallback to BeautifulSoup
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
            element.decompose()
        
        # Try common content selectors
        content_selectors = [
            'article', '[role="main"]', '.content', '.post-content', 
            '.article-body', '.entry-content', 'main', '.post', '.article'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                text = content_elem.get_text(separator=' ', strip=True)
                if len(text) > 200:
                    print(f"  ✅ Extracted content via BeautifulSoup ({selector})")
                    return text
        
        # Last resort - get all paragraphs
        paragraphs = soup.find_all('p')
        text = '\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
        
        if len(text) > 200:
            print(f"  ✅ Extracted content via paragraph fallback")
            return text
        
        print(f"  ⚠️ Content too short, using description fallback")
        return ""
        
    except Exception as e:
        print(f"  BeautifulSoup failed: {e}")
        return ""


def smart_content_extraction(article):
    """Use RSS description if good enough, otherwise scrape"""
    
    description = article.get('description', '')
    
    # Check if RSS description is substantial and useful
    if (len(description) > 150 and 
        not any(phrase in description.lower() for phrase in 
               ['read more', 'continue reading', 'click here', 'full story', 'learn more'])):
        print(f"Using RSS description for: {article['title'][:50]}...")
        return description
    
    # Extract full content if description is insufficient
    print(f"Extracting full content for: {article['title'][:50]}...")
    content = extract_content_free(article['link'])
    
    # Fallback to description if extraction fails
    if not content and description:
        print(f"  Using description as fallback")
        return description
    
    return content


def batch_summarize_articles(articles_with_content, cache):
    """Summarize multiple articles in one API call"""
    
    # Check cache first
    articles_to_summarize = []
    cached_summaries = {}
    
    for i, article in enumerate(articles_with_content):
        cached_summary = cache.get_summary(article['link'])
        if cached_summary:
            cached_summaries[i] = cached_summary
            print(f"Using cached summary for: {article['title'][:50]}...")
        else:
            articles_to_summarize.append((i, article))
    
    if not articles_to_summarize:
        print("All summaries found in cache!")
        return cached_summaries
    
    print(f"Generating summaries for {len(articles_to_summarize)} articles...")
    
    # Prepare batch prompt
    batch_prompt = "Create a one-line summary (max 25 words) for each article focusing on business impact and what's genuinely new:\n\n"
    
    for idx, (original_idx, article) in enumerate(articles_to_summarize):
        # Truncate content to avoid token limits
        content = article['content'][:1500] if article['content'] else "Content not available"
        batch_prompt += f"Article {idx + 1}:\nTitle: {article['title']}\nContent: {content}\n\n"
    
    batch_prompt += """
    Respond with ONLY numbered summaries in this exact format:
    1. [Summary for article 1]
    2. [Summary for article 2]
    3. [Summary for article 3]
    
    Focus on: what's new, why it matters, business implications.
    """
    
    client = OpenAI(base_url="https://api.fireworks.ai/inference/v1", api_key=FIREWORKS_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model="accounts/fireworks/models/llama4-scout-instruct-basic",
            messages=[
                {"role": "system", "content": "You are an expert at creating concise, business-focused AI summaries."},
                {"role": "user", "content": batch_prompt}
            ],
            temperature=0.1,
            max_tokens=1000  # Adjust based on number of articles
        )
        
        if response and response.choices and response.choices[0].message:
            summaries_text = response.choices[0].message.content.strip()
            
            # Parse numbered summaries
            summary_pattern = r'(\d+)\.\s*(.+?)(?=\n\d+\.|\n*$)'
            matches = re.findall(summary_pattern, summaries_text, re.DOTALL)
            
            new_summaries = {}
            for match in matches:
                list_idx = int(match[0]) - 1  # Convert to 0-based index
                summary = match[1].strip()
                
                if list_idx < len(articles_to_summarize):
                    original_idx, article = articles_to_summarize[list_idx]
                    new_summaries[original_idx] = summary
                    # Cache the summary
                    cache.set_summary(article['link'], summary)
            
            # Combine cached and new summaries
            all_summaries = {**cached_summaries, **new_summaries}
            print(f"✅ Generated {len(new_summaries)} new summaries, used {len(cached_summaries)} cached")
            return all_summaries
            
    except Exception as e:
        print(f"Error in batch summarization: {e}")
        # Return cached summaries at least
        return cached_summaries


def filter_summaries_with_ai(articles_with_summaries):
    """Filter out duplicates and poor quality summaries (unchanged)"""
    
    if len(articles_with_summaries) <= 1:
        return articles_with_summaries
    
    article_data = []
    for idx, article in enumerate(articles_with_summaries):
        article_data.append({
            "id": idx,
            "title": article["title"],
            "source": article["source"],
            "summary": article["summary"],
            "link": article["link"]
        })
    
    prompt = f"""Review these article summaries for duplicates and quality issues:

{json.dumps(article_data, indent=2)}

Return articles to KEEP as JSON:
{{"kept_articles": [list of articles to keep with all fields]}}

Remove duplicates and poor summaries. Include only high-quality, unique articles."""
    
    client = OpenAI(base_url="https://api.fireworks.ai/inference/v1", api_key=FIREWORKS_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model="accounts/fireworks/models/llama4-scout-instruct-basic",
            messages=[
                {"role": "system", "content": "You are an expert content curator who removes duplicates and poor content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        if response and response.choices and response.choices[0].message:
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON
            json_pattern = r'```json\s*(.*?)\s*```'
            json_match = re.search(json_pattern, result_text, re.DOTALL)
            
            if json_match:
                kept_json = json.loads(json_match.group(1))
                kept_articles = kept_json.get("kept_articles", [])
                
                result_articles = []
                for article in kept_articles:
                    result_articles.append({
                        "title": article.get("title", ""),
                        "source": article.get("source", ""),
                        "summary": article.get("summary", ""),
                        "link": article.get("link", "")
                    })
                
                removed_count = len(articles_with_summaries) - len(result_articles)
                print(f"AI filtering: kept {len(result_articles)}, removed {removed_count}")
                return result_articles
                
    except Exception as e:
        print(f"Error in AI filtering: {e}")
    
    return articles_with_summaries


def generate_pdf_report(articles):
    """Generate a professional PDF report with article summaries"""
    
    if not PDF_AVAILABLE:
        print("❌ ReportLab not installed. Cannot generate PDF.")
        print("Install with: pip install reportlab")
        return None
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = REPORTS_DIR / f"ai_news_digest_{timestamp}.pdf"
    
    print(f"📄 Generating PDF report: {filename}")
    
    try:
        # Create PDF document
        doc = SimpleDocTemplate(
            str(filename),
            pagesize=A4,
            topMargin=1*inch,
            bottomMargin=1*inch,
            leftMargin=1*inch,
            rightMargin=1*inch
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1a5490'),
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=HexColor('#666666'),
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        article_title_style = ParagraphStyle(
            'ArticleTitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#2c5aa0'),
            spaceBefore=20,
            spaceAfter=10,
            leftIndent=0
        )
        
        source_style = ParagraphStyle(
            'Source',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor('#888888'),
            spaceAfter=8,
            leftIndent=0
        )
        
        summary_style = ParagraphStyle(
            'Summary',
            parent=styles['Normal'],
            fontSize=11,
            textColor=HexColor('#333333'),
            spaceAfter=10,
            leftIndent=0,
            spaceBefore=5
        )
        
        link_style = ParagraphStyle(
            'Link',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor('#0066cc'),
            spaceAfter=20,
            leftIndent=0
        )
        
        # Build document content
        story = []
        
        # Title and metadata
        story.append(Paragraph("AI News & Research Digest", title_style))
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            subtitle_style
        ))
        story.append(Paragraph(
            f"Total Articles: {len(articles)}",
            subtitle_style
        ))
        
        story.append(Spacer(1, 20))
        
        # Add articles
        for i, article in enumerate(articles):
            # Article title
            story.append(Paragraph(article['title'], article_title_style))
            
            # Source
            story.append(Paragraph(f"Source: {article['source']}", source_style))
            
            # Summary
            story.append(Paragraph(f"<b>Summary:</b> {article['summary']}", summary_style))
            
            # Link
            story.append(Paragraph(
                f'<b>Read more:</b> <link href="{article["link"]}" color="blue">{article["link"]}</link>',
                link_style
            ))
            
            # Add separator line except for last article
            if i < len(articles) - 1:
                story.append(Spacer(1, 10))
                story.append(Paragraph("_" * 80, styles['Normal']))
                story.append(Spacer(1, 10))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            "Generated by AI News Aggregator - Optimized Version",
            ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=HexColor('#999999'),
                alignment=1
            )
        ))
        
        # Build PDF
        doc.build(story)
        
        print(f"✅ PDF report generated successfully: {filename}")
        return str(filename)
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        return None


def create_articles_csv(articles):
    """Create CSV file in reports directory with article information"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = REPORTS_DIR / f"ai_news_digest_{timestamp}.csv"
    
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Title', 'Source', 'Summary', 'Link', 'Generated_Date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for article in articles:
                writer.writerow({
                    'Title': article['title'],
                    'Source': article['source'],
                    'Summary': article['summary'],
                    'Link': article['link'],
                    'Generated_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        print(f"✅ CSV report generated: {csv_filename}")
        return str(csv_filename)
        
    except Exception as e:
        print(f"❌ Error generating CSV: {e}")
        return None


# HTML report generation removed for efficiency - PDF + CSV provide all needed functionality


def run_pipeline_optimized():
    """Streamlined pipeline - RSS feeds only, maximum efficiency!"""
    
    print("🚀 Starting STREAMLINED AI news pipeline...")
    print("=" * 50)
    
    # Initialize cache and state tracking
    cache = ArticleCache()
    state_tracker = StateTracker()
    
    # Step 1: Collect articles from RSS feeds only (all sources now have RSS!)
    print(f"\n📰 Collecting articles from {len(RSS_FEEDS)} RSS sources...")
    all_articles = fetch_rss_articles()
    print(f"Found {len(all_articles)} total articles")
    
    # Step 2: Filter out previously sent articles
    print("\n🔍 Filtering for new articles...")
    new_articles = state_tracker.filter_new_articles(all_articles)
    
    if not new_articles:
        print("✅ No new articles to process today!")
        return
    
    # Step 3: Smart content extraction (free when possible)
    print(f"\n📄 Extracting content for {len(new_articles)} articles...")
    articles_with_content = []
    
    for i, article in enumerate(new_articles):
        print(f"  [{i+1}/{len(new_articles)}] Processing: {article['title'][:50]}...")
        content = smart_content_extraction(article)
        
        if content:
            articles_with_content.append({
                **article, 
                'content': content[:2000]  # Limit content length
            })
        else:
            print(f"    ⚠️ Skipping article with no content")
    
    if not articles_with_content:
        print("❌ No articles with extractable content found.")
        return
    
    # Step 4: Batch summarization (major cost savings!)
    print(f"\n🤖 Generating summaries (batched for efficiency)...")
    summaries = batch_summarize_articles(articles_with_content, cache)
    
    # Step 5: Combine articles with summaries
    final_articles = []
    for i, article in enumerate(articles_with_content):
        if i in summaries:
            final_articles.append({
                'title': article['title'],
                'source': article['source'],
                'link': article['link'],
                'summary': summaries[i]
            })
    
    if not final_articles:
        print("❌ No articles were successfully summarized.")
        return
    
    # Step 6: AI-powered duplicate filtering
    print(f"\n🧹 Filtering for quality and duplicates...")
    filtered_articles = filter_summaries_with_ai(final_articles)
    
    if not filtered_articles:
        print("❌ No articles passed quality filtering.")
        return
    
    # Step 7: Generate reports
    print(f"\n📊 Generating reports with {len(filtered_articles)} articles...")
    
    # Generate PDF report (primary format)
    pdf_path = generate_pdf_report(filtered_articles)
    
    # Generate CSV report (for data analysis)
    csv_path = create_articles_csv(filtered_articles)
    
    # Skip HTML report to reduce complexity and storage
    html_path = None
    
    # Step 8: Mark articles as sent
    sent_urls = [article['link'] for article in filtered_articles]
    state_tracker.mark_articles_sent(sent_urls)
    
    print("\n✅ STREAMLINED PIPELINE COMPLETED!")
    print(f"📊 Final stats:")
    print(f"   • RSS sources: {len(RSS_FEEDS)}")
    print(f"   • Articles collected: {len(all_articles)}")
    print(f"   • New articles: {len(new_articles)}")
    print(f"   • Successfully processed: {len(final_articles)}")
    print(f"   • Final digest: {len(filtered_articles)} articles")
    print(f"   • Estimated API calls: ~2-3 (vs ~25-45 in original!)")
    print(f"   • Cost savings: ~90-95% 🎉")
    
    print(f"\n📁 Reports generated:")
    if pdf_path:
        print(f"   • PDF: {pdf_path}")
    if csv_path:
        print(f"   • CSV: {csv_path}")
    print(f"   • HTML generation disabled for efficiency")
    
    return {
        "pdf_report": pdf_path,
        "csv_report": csv_path,
        "articles_count": len(filtered_articles)
    }


def test_optimizations():
    """Test the optimization components"""
    print("🧪 Testing streamlined components...")
    
    # Test cache
    cache = ArticleCache()
    test_url = "https://example.com/test"
    cache.set_summary(test_url, "Test summary")
    retrieved = cache.get_summary(test_url)
    print(f"✅ Cache test: {retrieved == 'Test summary'}")
    
    # Test state tracker
    state = StateTracker()
    test_articles = [{"link": "https://example.com/article1", "title": "Test"}]
    new_articles = state.filter_new_articles(test_articles)
    print(f"✅ State tracker test: {len(new_articles) == 1}")
    
    # Test content extraction
    if NEWSPAPER_AVAILABLE:
        print("✅ Newspaper3k available for content extraction")
    else:
        print("⚠️ Newspaper3k not available, will use BeautifulSoup fallback")
    
    # Test PDF generation
    if PDF_AVAILABLE:
        print("✅ ReportLab available for PDF generation")
    else:
        print("⚠️ ReportLab not available, install with: pip install reportlab")
    
    # Test reports directory
    if REPORTS_DIR.exists():
        print(f"✅ Reports directory ready: {REPORTS_DIR}")
    else:
        print(f"❌ Reports directory not found: {REPORTS_DIR}")
    
    # Test RSS feeds
    print(f"✅ RSS sources configured: {len(RSS_FEEDS)}")
    print("✅ Blog scraping removed - maximum efficiency!")
    
    print("🧪 All streamlined tests completed!")


def clean_old_reports(days_to_keep=7):
    """Clean up old report files to save disk space"""
    if not REPORTS_DIR.exists():
        return
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    cleaned_count = 0
    
    for file_path in REPORTS_DIR.glob("*"):
        if file_path.is_file():
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_time < cutoff_date:
                try:
                    file_path.unlink()
                    cleaned_count += 1
                except Exception as e:
                    print(f"Warning: Could not delete {file_path}: {e}")
    
    if cleaned_count > 0:
        print(f"🧹 Cleaned up {cleaned_count} old report files")


if __name__ == "__main__":
    # Uncomment to test optimizations
    # test_optimizations()
    
    # Clean up old reports (optional)
    # clean_old_reports(days_to_keep=7)
    
    # Run the streamlined pipeline (no async needed!)
    result = run_pipeline_optimized()
    
    if result and result.get("articles_count", 0) > 0:
        print(f"\n🎉 Successfully generated reports with {result['articles_count']} articles!")
        print("📂 Check the 'reports' folder for your generated files.")
    else:
        print("\n💤 No new articles found today. No reports generated.")