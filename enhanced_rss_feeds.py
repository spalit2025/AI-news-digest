# Enhanced RSS Feed Configuration with Validation
# Focus on high-quality, working AI news sources

import requests
import feedparser
from datetime import datetime
import time
from typing import Dict, List, Optional, Tuple

class RSSFeedValidator:
    """Validates and maintains RSS feed health"""
    
    def __init__(self):
        self.validation_cache = {}
        self.last_validation = None
    
    def validate_feed(self, url: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate RSS feed and return status
        Returns: (is_valid, status_message, redirect_url)
        """
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                # Additional validation - check if it's actually RSS
                feed_response = requests.get(url, timeout=10)
                feed = feedparser.parse(feed_response.content)
                
                if feed.entries:
                    return True, f"✅ Active ({len(feed.entries)} entries)", None
                else:
                    return False, "❌ No entries found", None
            
            elif response.status_code == 301 or response.status_code == 302:
                return True, f"🔄 Redirected to {response.url}", response.url
            
            else:
                return False, f"❌ HTTP {response.status_code}", None
                
        except Exception as e:
            return False, f"❌ Error: {str(e)[:50]}...", None
    
    def validate_all_feeds(self, feeds: Dict[str, str]) -> Dict[str, Dict]:
        """Validate all feeds and return detailed status"""
        results = {}
        
        for source, url in feeds.items():
            is_valid, message, redirect_url = self.validate_feed(url)
            results[source] = {
                'url': url,
                'is_valid': is_valid,
                'status': message,
                'redirect_url': redirect_url,
                'validated_at': datetime.now().isoformat()
            }
            time.sleep(0.5)  # Be respectful to servers
        
        return results

# Enhanced RSS Feed Configuration
# Prioritizing working, high-quality AI sources

ENHANCED_RSS_FEEDS = {
    # Core AI Companies (Working Sources)
    "OpenAI": "https://openai.com/news/rss.xml",
    "Hugging Face": "https://huggingface.co/blog/feed.xml",
    "Anthropic": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic.xml",
    
    # Research & Academic
    "DeepMind": "https://deepmind.com/blog/feed/basic",
    "AI Research": "https://ai.googleblog.com/feeds/posts/default",
    "MIT Technology Review AI": "https://www.technologyreview.com/feed/",
    "Stanford AI Lab": "https://ai.stanford.edu/blog/feed/",
    
    # Industry & Business
    "VentureBeat AI": "https://venturebeat.com/ai/feed/",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Information AI": "https://www.theinformation.com/briefings/artificial-intelligence/feed",
    
    # Specialized AI Sources
    "Towards Data Science": "https://towardsdatascience.com/feed",
    "AI News": "https://artificialintelligence-news.com/feed/",
    "Machine Learning Mastery": "https://machinelearningmastery.com/feed/",
    
    # Company Specific (Updated URLs)
    "NVIDIA Developer": "https://developer.nvidia.com/blog/feed/",
    "Meta AI Research": "https://research.facebook.com/feed/",
    "Microsoft AI": "https://blogs.microsoft.com/ai/feed/",
    "Google AI": "https://blog.google/technology/ai/rss/",
    
    # Startup & Investment
    "AI Startups": "https://aimagazine.com/feed",
    "CB Insights AI": "https://www.cbinsights.com/research/briefing/artificial-intelligence/feed/",
}

# Alternative URLs for problematic feeds
FALLBACK_FEEDS = {
    "NVIDIA": [
        "https://developer.nvidia.com/blog/feed/",
        "https://blogs.nvidia.com/feed/",
        "https://nvidianews.nvidia.com/Feeds/RSSFeed.aspx"
    ],
    "Google AI": [
        "https://blog.google/technology/ai/rss/",
        "https://ai.googleblog.com/feeds/posts/default",
        "https://research.google/feeds/publications.xml"
    ],
    "Meta AI": [
        "https://research.facebook.com/feed/",
        "https://ai.meta.com/blog/feed/",
        "https://about.fb.com/news/category/ai/feed/"
    ]
}

# Feed Categories for Better Organization
FEED_CATEGORIES = {
    "research": ["DeepMind", "AI Research", "Stanford AI Lab", "Meta AI Research"],
    "industry": ["OpenAI", "Hugging Face", "Anthropic", "NVIDIA Developer"],
    "news": ["VentureBeat AI", "TechCrunch AI", "MIT Technology Review AI"],
    "technical": ["Towards Data Science", "Machine Learning Mastery", "AI News"],
    "business": ["The Information AI", "CB Insights AI", "AI Startups"]
}

# Quality Metrics for Feed Scoring
FEED_QUALITY_METRICS = {
    "OpenAI": {"authority": 10, "frequency": 8, "technical_depth": 9},
    "Hugging Face": {"authority": 9, "frequency": 9, "technical_depth": 8},
    "Anthropic": {"authority": 9, "frequency": 6, "technical_depth": 9},
    "DeepMind": {"authority": 10, "frequency": 7, "technical_depth": 10},
    "VentureBeat AI": {"authority": 7, "frequency": 9, "technical_depth": 6},
    "TechCrunch AI": {"authority": 8, "frequency": 10, "technical_depth": 5},
    "MIT Technology Review AI": {"authority": 9, "frequency": 8, "technical_depth": 8},
}

def get_prioritized_feeds(max_feeds: int = 10) -> Dict[str, str]:
    """
    Return prioritized list of feeds based on quality metrics
    """
    # Sort feeds by combined quality score
    scored_feeds = []
    
    for source, url in ENHANCED_RSS_FEEDS.items():
        metrics = FEED_QUALITY_METRICS.get(source, {"authority": 5, "frequency": 5, "technical_depth": 5})
        score = sum(metrics.values()) / len(metrics)
        scored_feeds.append((score, source, url))
    
    # Sort by score (highest first) and return top feeds
    scored_feeds.sort(reverse=True)
    return {source: url for _, source, url in scored_feeds[:max_feeds]}

def validate_and_fix_feeds() -> Dict[str, str]:
    """
    Validate current feeds and attempt to fix broken ones
    """
    validator = RSSFeedValidator()
    validation_results = validator.validate_all_feeds(ENHANCED_RSS_FEEDS)
    
    fixed_feeds = {}
    
    for source, result in validation_results.items():
        if result['is_valid']:
            fixed_feeds[source] = result['url']
        else:
            # Try fallback URLs if available
            if source in FALLBACK_FEEDS:
                for fallback_url in FALLBACK_FEEDS[source]:
                    is_valid, message, redirect_url = validator.validate_feed(fallback_url)
                    if is_valid:
                        print(f"✅ Fixed {source} with fallback URL: {fallback_url}")
                        fixed_feeds[source] = fallback_url
                        break
            
            if source not in fixed_feeds:
                print(f"❌ Could not fix {source}: {result['status']}")
    
    return fixed_feeds

if __name__ == "__main__":
    # Test the enhanced feeds
    print("🔍 Validating Enhanced RSS Feeds...")
    print("=" * 60)
    
    validator = RSSFeedValidator()
    results = validator.validate_all_feeds(ENHANCED_RSS_FEEDS)
    
    working_feeds = 0
    total_feeds = len(results)
    
    for source, result in results.items():
        print(f"{source:<25} {result['status']}")
        if result['is_valid']:
            working_feeds += 1
    
    print(f"\n📊 Summary: {working_feeds}/{total_feeds} feeds working ({working_feeds/total_feeds*100:.1f}%)")
    
    # Get prioritized feeds
    print(f"\n🎯 Top 10 Prioritized Feeds:")
    prioritized = get_prioritized_feeds(10)
    for i, (source, url) in enumerate(prioritized.items(), 1):
        print(f"{i:2d}. {source}") 