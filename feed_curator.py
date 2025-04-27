# Author: Sanjay Sathyapriyan March 15 2025

import feedparser
import smtplib
from openai import OpenAI
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import csv
import os
from datetime import datetime, timedelta
import asyncio
import json
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field
import io
import time
from dotenv import load_dotenv

load_dotenv()

RSS_FEEDS ={  
"Wired AI":"https://www.wired.com/feed/tag/ai/latest/rss",
"TechCrunch AI":"https://techcrunch.com/tag/artificial-intelligence/feed/",
"MIT Tech Review":"https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml",
"ArXiv AI":"http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=2",
"Hugging Face Blog":"https://huggingface.co/blog/feed.xml"
 }

BLOG_URLS ={
"Papers with code":"https://paperswithcode.com/latest",
"Towards Data Science": "https://towardsdatascience.com/",
"Stability AI research":"https://stability.ai/research",
"Anthropic":"https://www.anthropic.com/news"
}

FIREWORKS_API_KEY=os.getenv("FIREWORKS_API_KEY")

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")

EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") 
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

class ArticleSummaryFilter(BaseModel):
    filtered_articles: List[dict] = Field(description="List of unique, high-quality articles to keep")
    removed_articles: List[dict] = Field(description="List of duplicate or erroneous articles that were removed")
    
async def filter_summaries_with_ai(articles_with_summaries):
    """
    Uses DeepSeek to filter out duplicate and erroneous summaries
    Returns two separate JSON objects with complete article details
    """
    print("\nFiltering summaries for duplicates and quality issues...")
    
    # Skip if there are too few articles
    if len(articles_with_summaries) <= 1:
        return articles_with_summaries
    
    # Create a list of article data for review
    article_data = []
    for idx, article in enumerate(articles_with_summaries):
        article_data.append({
            "id": idx,
            "title": article["title"],
            "source": article["source"],
            "description": article["description"],
            "link": article["link"]
        })
    
    # Create the prompt for DeepSeek requesting two separate JSONs with complete article details
    prompt = f"""Review these article summaries for duplicates and quality issues:

{json.dumps(article_data, indent=2)}

TASK:
1. Identify duplicate or nearly identical articles (same content covered differently)
2. Identify summaries that are erroneous (summary not present, unclear, generic)
3. Divide articles into two groups: KEEP and REMOVE
4. Duplicate items and items with erroneous summaries should be stored in removed_articles JSON
5. Return removed_articles JSON even if it is empty

RETURN EXACTLY TWO JSON OBJECTS:

First JSON - ARTICLES TO KEEP:
```json
{{
  "kept_articles": [
    {{
      "id": 0,
      "title": "Example Title",
      "source": "Source Name",
      "description": "Short Description of the text",
      "link": "https://example.com/article",
    }}
  ]
}}
```

Second JSON - ARTICLES TO REMOVE:
```json
{{
  "removed_articles": [
    {{
      "id": 1,
      "title": "Example Duplicate",
      "source": "Source Name",
      "summary": "The complete summary text",
      "link": "https://example.com/duplicate",
      "reason": "Duplicate of article 0 or Incorrect Summary" 
    }}
  ]
}}
```

REQUIREMENTS:
- Include ALL article details (id, title, source, summary, link) in both JSONs
- IDs must match the original article indices
- Include a brief reason for each removal decision
- Format each JSON exactly as shown above
- Return both JSONs even if one category is empty
- Each JSON must be valid and complete on its own
"""
    
    client = OpenAI(base_url = "https://api.fireworks.ai/inference/v1",
                   api_key=FIREWORKS_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model="accounts/fireworks/models/llama4-scout-instruct-basic",
            messages=[
                {"role": "system", "content": "You are an expert content curator who identifies, removes duplicate and content with erroneous summaries. You provide clear, structured output responses with valid JSON that includes all requested fields."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=8000  # Increased for larger JSON responses
        )
        
        # Parse the response
        if response and response.choices and response.choices[0].message:
            result_text = response.choices[0].message.content.strip()
            
            # Extract the two JSON objects using regex
            import re
            json_pattern = r'```json\s*(.*?)\s*```'
            json_matches = re.findall(json_pattern, result_text, re.DOTALL)
            
            if len(json_matches) < 2:
                print("Error: Expected two JSON objects in response, found", len(json_matches))
                print("Response was:", result_text[:200] + "..." if len(result_text) > 200 else result_text)
                return articles_with_summaries
            
            # Parse the JSON objects
            try:
                kept_json = json.loads(json_matches[0])
                removed_json = json.loads(json_matches[1])
                #print("kept json",kept_json)
                print("removed_jsons", removed_json)
                
                # Use the complete kept articles data
                kept_articles = kept_json.get("kept_articles", [])

                
                # Print removal information with details
                removed_articles = removed_json.get("removed_articles", [])
                print(f"\nFiltered out {len(removed_articles)} articles:")
                
                for article in removed_articles:
                    article_id = article.get("id")
                    title = article.get("title", f"Article {article_id}")
                    reason = article.get("reason", "No reason provided")
                    print(f"- {title}: {reason}")
                
                # Convert kept articles format to match expected structure
                result_articles = []
                for article in kept_articles:
                    result_articles.append({
                        "title": article.get("title", ""),
                        "source": article.get("source", ""),
                        "description": article.get("description", ""),
                        "link": article.get("link", "")
                    })
                
                # Safety check - if no articles to keep, return all
                if not result_articles:
                    print("Warning: No articles left after filtering. Using all articles.")
                    return articles_with_summaries
                
                print(f"\nKept {len(result_articles)} articles after LLM filtering.")
                return result_articles
                
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {e}")
                print("JSON text was:", json_matches[0][:100] + "..." if len(json_matches[0]) > 100 else json_matches[0])
                return articles_with_summaries
                
    except Exception as e:
        print(f"Error filtering summaries: {e}")
        # Return original list if filtering fails
        return articles_with_summaries
    
    return articles_with_summaries  # Fallback

# 2. Fetch articles from RSS feeds
def fetch_rss_articles():
    articles = []
    current_time = datetime.now()
    cutoff_time = current_time - timedelta(days=7)

    for source, url in RSS_FEEDS.items():
        print(f"Fetching RSS feed: {url}")
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                print(f"Warning: No entries found in {url}")
        except Exception as e:
            print(f"Error fetching RSS feed {url}: {e}")
            continue
        for entry in feed.entries[:2]:  # Limit to the 2 most recent articles per source
            title = entry.title
            link = entry.link
            # Get description from either 'description' or 'summary' field
            description = entry.get('description', entry.get('summary', ''))
            # Clean up description by removing HTML tags if present
            description = description.replace('<p>', '').replace('</p>', '')
            if hasattr(entry, 'published_parsed'):
                published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            else:
                # If no date available, skip this entry
                print(f"Warning: No date information for {title}. Skipping.")
                continue
                
            # Check if the article is within the last 24 hours
            if published_time >= cutoff_time:
                print(f"Found recent article: {link} (Published: {published_time})")
                articles.append({"source": source, "title": title, "link": link,"description":description})
            else:
                print(f"Skipping older article: {link} (Published: {published_time})")
    
    return articles

# New class for blog article extraction
class ArticleLink(BaseModel):
    url: str = Field(description="The full URL of the article")
    title: str = Field(description="The title of the article")
    published_date: datetime = Field(description="The published date of the article")
    description: str = Field(description="The short description of the article")

# New function for blog scraping
async def   fetch_blog_articles():
    articles = []
    print("\nStarting blog extraction...")

    current_time = datetime.now()
    cutoff_time = current_time.date() - timedelta(days=7)

    for source, url in BLOG_URLS.items():
        print(f"Scraping blog: {url}")
        try:
            llm_strategy = LLMExtractionStrategy(
                provider="fireworks_ai/accounts/fireworks/models/deepseek-v3",
                api_token=FIREWORKS_API_KEY,
                schema=ArticleLink.model_json_schema(),
                extraction_type="schema",
                instruction=f"""Analyze the webpage and extract EXACTLY 2 of the most recent articles published on or after {cutoff_time} .
                The current date is {current_time.date()}.
                                
                EXTRACTION PRIORITIES:
                1. Include articles published exactly on {cutoff_time} or any time after
                2. Sort by recency - newest articles first     
                
                REQUIRED EXTRACTION FORMAT:
                - Each article must include FULL URL (not relative paths), exact title, and published_date and short_description of the article
                - URLs must be complete, valid, and directly lead to the article (not section pages)
                - P ublished_date must be in YYYY-MM-DD format
                
                IMPORTANT RULES:
                - Return EXACTLY 2 articles if available (fewest if less than 2 exist)
                - Return empty JSON if no articles from {cutoff_time} or later are found
                - Verify all URLs are properly formatted and valid before returning
                - Extract direct article links, not category pages or list views
                
                Focus on extracting articles published on {cutoff_time} or more recently.""",
                chunk_token_threshold=1000,
                overlap_rate=0.1,
                apply_chunking=True,
                input_format="markdown",
                extra_args={"temperature": 0.1, "max_tokens": 1000},
            )

            crawl_config = CrawlerRunConfig(
                extraction_strategy=llm_strategy,
                cache_mode=CacheMode.BYPASS,
                process_iframes=False,
                remove_overlay_elements=True,
                exclude_external_links=True,
            )

            browser_cfg = BrowserConfig(headless=True, verbose=True)

            async with AsyncWebCrawler(config=browser_cfg) as crawler:
                result = await crawler.arun(url=url, config=crawl_config)

                if result.success:
                    blog_data = json.loads(result.extracted_content)
                    print(f"Extracted {len(blog_data)} articles from {url}")
                    print(blog_data)
                    
                    # Add each extracted article to our list
                    for article in blog_data:
                        try:
                            pub_date = datetime.strptime(article['published_date'], '%Y-%m-%d').date()
                            
                            # Check if article is recent enough
                            if pub_date >= cutoff_time:
                                print(f"Found blog article: {article['url']}")
                                article["url"].replace("</","")
                                article["url"].replace(">","")
                        
                                articles.append({
                                    "source": source,
                                    "title": article["title"],
                                    "link": article["url"],
                                    "description": article["description"]
                                })
                            else:
                                print(f"Skipping older article: {article['title']} (Published: {pub_date})")
                        except ValueError as e:
                            print(f"Error parsing date for {article.get('title', 'unknown article')}: {e}")                        

                    llm_strategy.show_usage()
                else:
                    print(f"Error scraping {url}: {result.error_message}")

        except Exception as e:
            print(f"Error processing blog {url}: {e}")

    print(f"\nFound {len(articles)} blog articles")
    return articles

# New class for article content extraction
class ArticleContent(BaseModel):
    content: str 
    error: str

#New function for scraping article content
async def scrape_article_content(url):
    print(f"Scraping content from: {url}")
    try:
        llm_strategy = LLMExtractionStrategy(
            provider="fireworks_ai/accounts/fireworks/models/deepseek-v3",
            api_token=FIREWORKS_API_KEY,
            schema=ArticleContent.model_json_schema(),
            extraction_type="schema",
            instruction="""Extract ONLY the main article content from this webpage in clean, plain text format.

			   EXTRACTION RULES:
			   1. INCLUDE ONLY the article's main body text, key quotes, and essential information
			   2. Preserve paragraph structure and logical flow of ideas
			   3. Include section headings that are part of the article's content structure
			   4. Maintain the original meaning and context of the content
			   
			   STRICTLY EXCLUDE:
			   - Navigation menus, breadcrumbs, and site headers/footers
			   - Sidebars, related articles sections, and recommendation widgets
			   - Author bios, social media buttons, and sharing options
			   - ALL advertisements, promotional content, and sponsored links
			   - Comment sections and user-generated feedback
			   - Cookie notices, GDPR warnings, and other popups
			   - Any HTML/CSS/JavaScript code snippets (unless they're the article's subject)
			   - Image captions and alt text (unless critical to understanding)
			   - Pagination controls and "read more" buttons
			   
			   FORMAT REQUIREMENTS:
			   - Deliver clean, continuous text with proper paragraph breaks
			   - Remove any extraneous whitespace, special characters, or formatting artifacts
			   - Ensure the content reads naturally and coherently
			   - Detect and preserve only the substantive content of the article
			   
			   This extraction should result in ONLY the actual article content that would be of interest to a reader.""",
            chunk_token_threshold=1000,
            overlap_rate=0.1,
            apply_chunking=False,
            input_format="markdown",
            extra_args={"temperature": 0.1, "max_tokens": 2000},
        )

        crawl_config = CrawlerRunConfig(
            extraction_strategy=llm_strategy,
            cache_mode=CacheMode.BYPASS,
            process_iframes=False,
            remove_overlay_elements=True,
            exclude_external_links=True,
        )

        browser_cfg = BrowserConfig(headless=True,text_mode=True, verbose=True)

        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=url, config=crawl_config)

            if result.success:
                content_data = json.loads(result.extracted_content)
                print(f"Successfully extracted content from {url}")
                llm_strategy.show_usage()
                # Handle both list and dictionary responses
                if isinstance(content_data, dict):
                   return content_data.get("content", "")
                elif isinstance(content_data, list) and content_data:
                   # If it's a list, try to get the first item's content
                   if isinstance(content_data[0], dict):
                       return content_data[0].get("content", "")
                   # If it's a string or other direct value
                   elif isinstance(content_data[0], str):
                       return content_data[0]
               # Return empty string if we couldn't extract content
                return ""
                
                
            else:
                print(f"Error scraping content from {url}: {result.error_message}")
                return ""

    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
        return ""

    
def summarize_article(title, link, content):
    
    if not isinstance(title, str) or not isinstance(link, str):
        print(f"Invalid input types - Title type: {type(title)}, Link type: {type(link)}")
        return "Summary not available: Invalid input"
    
    print(f"Attempting to summarize: {link}")
    
    # If no content was scraped, use a fallback message
    if not content or len(content.strip()) < 100:
        content_text = "Content could not be extracted. Using title only."
        print(f"Warning: No substantive content extracted for {link}")
    else:
        # Truncate very long content to avoid token limits
        max_content_length = 10000
        content_text = content[:max_content_length] + ("..." if len(content) > max_content_length else "")
    
    prompt = f""""This is an article with title: "{title}" and content: {content_text}

		Extract a brief summary of the article in one line (max 25 words). Focus on:
		- What makes this truly noteworthy
		- Why it matters
		- What's genuinely new/different

		Format: "Summary: (specific innovation/finding and why it's significant)"
		"""
   
    client = OpenAI(base_url = "https://api.fireworks.ai/inference/v1",
    api_key=FIREWORKS_API_KEY)
    try:
        response = client.chat.completions.create(
            model="accounts/fireworks/models/llama4-scout-instruct-basic",
            messages=[{"role": "system", "content": "You are an AI strategic advisor who synthesizes technical developments for decision-makers. \
                       Your role is to extract business-relevant insights from technical AI content while maintaining accuracy.\
                       Focus on strategic implications, competitive advantages, and potential market impact. \
                       Provide balanced analysis that connects technical capabilities to business value.\
                        Ground your answers in real world information and data."},
                      {"role": "user", "content": prompt}],
                      temperature=0.1,
                      max_tokens=150
        )
        if response and response.choices and response.choices[0].message:
            summary = response.choices[0].message.content.strip()
            if summary:
                print(f"Successfully summarized: {link}")
                return summary
            
        print(f"Failed to summarize (empty response): {link}")
        return "Summary not available: Empty response"
        
    except Exception as e:
        print(f"Error summarizing {link}: {e}")
        return "Summary not available."

async def create_email_content(articles):
    email_body = "<h2>Daily AI News & Research Updates</h2>"
    failed_urls = []
    articles_with_summaries = []

    filtered_articles = await filter_summaries_with_ai(articles)

    print(f"\nKept {len(filtered_articles)} out of {len(articles)} articles after LLM-based filtering")

    # First, extract content and generate summaries
    for article in filtered_articles:
        # Scrape the article content
        content = await scrape_article_content(article["link"])

        # Summarize using the content
        summary = summarize_article(article["title"], article["link"], content)

        if "Summary not available" in summary:
            failed_urls.append(article["link"])
        else:
            # Add summary to article object
            article_with_summary = {
                "source": article["source"],
                "title": article["title"],
                "link": article["link"],
                "summary": summary
            }
            articles_with_summaries.append(article_with_summary)

    # Filter summaries to remove duplicates and erroneous ones
    #filtered_articles = await filter_summaries_with_ai(articles_with_summaries)
    
    #print(f"\nKept {len(filtered_articles)} out of {len(articles_with_summaries)} articles after LLM-based filtering")

    # Create the email with filtered articles
    for article in articles_with_summaries:
        email_body += f"<p><strong>{article['title']}</strong> ({article['source']})<br>{article['summary']}<br><a href='{article['link']}'>Read more</a></p>"
        
    if failed_urls:
        print("URLs that failed to summarize:")        
        for url in failed_urls:
            print(f"- {url}")
            
    return email_body,articles_with_summaries

def create_articles_csv(articles):
    """
    Creates a CSV file in memory with article information
    """
    output = io.StringIO()
    fieldnames = ['Title', 'Source', 'Summary', 'Link']
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for article in articles:
        writer.writerow({
            'Title': article['title'],
            'Source': article['source'],
            'Summary': article['summary'],
            'Link': article['link']
        })
    
    return output.getvalue()

# 5. Send Email
def send_email(content,filtered_articles):
    recipient_list = [email.strip() for email in EMAIL_RECIPIENT.split(';')]
    print("EMAIL Recipient",EMAIL_RECIPIENT)
    print("recipient list",recipient_list)
    
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(recipient_list)
    msg["Subject"] = "Daily AI News & Research Digest"
    print("to",msg["To"])

    msg.attach(MIMEText(content, "html"))
    
    csv_data = create_articles_csv(filtered_articles)
    csv_attachment = MIMEBase('application', 'octet-stream')
    csv_attachment.set_payload(csv_data.encode('utf-8'))
    encoders.encode_base64(csv_attachment)
    csv_attachment.add_header(
        'Content-Disposition', 
        f'attachment; filename=ai_news_digest_{datetime.now().strftime("%Y%m%d")}.csv'
    )

    msg.attach(csv_attachment)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, recipient_list, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

async def run_pipeline():
    # Run RSS feed extraction
    rss_articles = fetch_rss_articles()
    print("rss are ", rss_articles)

    # Run blog post extraction
    blog_articles = await fetch_blog_articles()
    print("blogs are ", blog_articles)

    # Combine the articles
    all_articles = rss_articles + blog_articles
    print(f"\nTotal articles found: {len(all_articles)}")

    # Create email content with all articles (includes content scraping, summarization, and LLM-based filtering)
    print("\nBeginning article processing and filtering...")
    email_content,filtered_articles = await create_email_content(all_articles)

    # Send the email
    print("\nSending email digest...")
    send_email(email_content,filtered_articles)
    print("Process completed.")

# Main Execution
if __name__ == "__main__":
    asyncio.run(run_pipeline())
