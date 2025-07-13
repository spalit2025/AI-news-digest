# Enhanced AI Summarization System
# Focus on high-quality, intelligent, business-focused summaries

import os
import time
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from openai import OpenAI
import requests

# Rate limiting configuration
RATE_LIMIT_DELAY = 2  # seconds between API calls
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

@dataclass
class ArticleAnalysis:
    title: str
    source: str
    link: str
    summary: str
    impact_score: int  # 1-10 scale
    category: str  # breakthrough, product_launch, funding, research, etc.
    companies: List[str]
    technologies: List[str]
    market_implications: str
    investment_angle: str
    sentiment: str  # positive, negative, neutral
    confidence: float  # 0-1 scale

class EnhancedSummarizer:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=api_key
        )
        self.last_api_call = 0
        
    def _rate_limited_api_call(self, messages: List[Dict], max_tokens: int = 1000) -> Optional[str]:
        """Make API call with rate limiting and retry logic"""
        for attempt in range(MAX_RETRIES):
            try:
                # Rate limiting
                time_since_last = time.time() - self.last_api_call
                if time_since_last < RATE_LIMIT_DELAY:
                    time.sleep(RATE_LIMIT_DELAY - time_since_last)
                
                response = self.client.chat.completions.create(
                    model="accounts/fireworks/models/llama4-scout-instruct-basic",
                    messages=messages,
                    temperature=0.1,
                    max_tokens=max_tokens
                )
                
                self.last_api_call = time.time()
                
                if response and response.choices and response.choices[0].message:
                    return response.choices[0].message.content.strip()
                else:
                    return None
                    
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    wait_time = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    print(f"Rate limit hit, waiting {wait_time} seconds before retry {attempt + 1}/{MAX_RETRIES}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"API error on attempt {attempt + 1}: {error_msg}")
                    if attempt == MAX_RETRIES - 1:
                        return None
                    time.sleep(RETRY_DELAY)
        
        return None
    
    def analyze_article(self, article: Dict) -> ArticleAnalysis:
        """Analyze a single article with comprehensive AI analysis"""
        
        # Prepare content for analysis
        content = article.get('content', '')[:1500]  # Limit content length
        title = article.get('title', '')
        source = article.get('source', '')
        link = article.get('link', '')
        
        # Single comprehensive analysis prompt to reduce API calls
        comprehensive_prompt = f"""You are analyzing an AI/tech article. Please respond with ONLY valid JSON.

ARTICLE:
Title: {title}
Source: {source}
Content: {content[:1000]}

RESPONSE FORMAT (copy exactly):
{{
"summary": "Brief summary of what's new and why it matters",
"impact_score": 6,
"category": "research",
"companies": ["OpenAI"],
"technologies": ["AI"],
"market_implications": "Brief market impact description",
"investment_angle": "Brief investment considerations",
"sentiment": "positive",
"confidence": 0.7
}}

Respond with ONLY the JSON above. No other text."""
        
        messages = [
            {"role": "system", "content": "You are a JSON API. Respond only with valid JSON. No explanations or additional text."},
            {"role": "user", "content": comprehensive_prompt}
        ]
        
        print(f"📊 Analyzing article: {title[:50]}...")
        
        response = self._rate_limited_api_call(messages, max_tokens=1500)
        
        if not response:
            print(f"❌ Failed to analyze article: {title[:50]}")
            return self._create_fallback_analysis(article)
        
        try:
            # Clean the response
            cleaned_response = response.strip()
            
            # Try multiple JSON extraction methods
            analysis_data = None
            
            # Method 1: Direct JSON parsing
            try:
                analysis_data = json.loads(cleaned_response)
            except json.JSONDecodeError:
                pass
            
            # Method 2: Extract JSON from code blocks
            if not analysis_data:
                json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned_response, re.DOTALL)
                if json_match:
                    try:
                        analysis_data = json.loads(json_match.group(1).strip())
                    except json.JSONDecodeError:
                        pass
            
            # Method 3: Find JSON object in text
            if not analysis_data:
                json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                if json_match:
                    try:
                        analysis_data = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        pass
            
            # If we successfully parsed JSON, create analysis
            if analysis_data:
                return ArticleAnalysis(
                    title=title,
                    source=source,
                    link=link,
                    summary=str(analysis_data.get('summary', 'Summary not available'))[:500],
                    impact_score=min(10, max(1, int(analysis_data.get('impact_score', 5)))),
                    category=str(analysis_data.get('category', 'industry_news')),
                    companies=analysis_data.get('companies', [])[:5],  # Limit to 5
                    technologies=analysis_data.get('technologies', [])[:5],  # Limit to 5
                    market_implications=str(analysis_data.get('market_implications', 'Market implications not available'))[:300],
                    investment_angle=str(analysis_data.get('investment_angle', 'Investment angle not available'))[:300],
                    sentiment=str(analysis_data.get('sentiment', 'neutral')),
                    confidence=min(1.0, max(0.0, float(analysis_data.get('confidence', 0.7))))
                )
            else:
                raise ValueError("Could not parse JSON from response")
            
        except Exception as e:
            print(f"❌ Error parsing response for {title[:50]}: {e}")
            print(f"Response was: {response[:200]}...")
            return self._create_fallback_analysis(article)
    
    def _create_fallback_analysis(self, article: Dict) -> ArticleAnalysis:
        """Create a basic analysis when AI analysis fails"""
        return ArticleAnalysis(
            title=article.get('title', 'Unknown Title'),
            source=article.get('source', 'Unknown Source'),
            link=article.get('link', ''),
            summary=article.get('description', 'AI analysis failed - using basic description'),
            impact_score=5,
            category='industry_news',
            companies=[],
            technologies=['AI'],
            market_implications='Analysis not available due to rate limiting',
            investment_angle='Analysis not available due to rate limiting',
            sentiment='neutral',
            confidence=0.3
        )
    
    def batch_analyze_articles(self, articles: List[Dict]) -> List[ArticleAnalysis]:
        """Analyze multiple articles with better rate limiting"""
        analyses = []
        
        print(f"🔍 Starting enhanced analysis of {len(articles)} articles...")
        
        for i, article in enumerate(articles):
            print(f"📊 Analyzing article {i+1}/{len(articles)}: {article.get('title', 'Unknown')[:50]}...")
            
            analysis = self.analyze_article(article)
            analyses.append(analysis)
            
            # Add delay between articles to respect rate limits
            if i < len(articles) - 1:  # Don't sleep after the last article
                time.sleep(RATE_LIMIT_DELAY)
        
        print(f"✅ Enhanced analysis completed for {len(analyses)} articles")
        return analyses
    
    def generate_trend_analysis(self, analyses: List[ArticleAnalysis]) -> Dict:
        """Generate trend analysis from multiple article analyses"""
        
        if not analyses:
            return {"error": "No articles to analyze"}
        
        # Prepare trend analysis prompt
        articles_summary = []
        for analysis in analyses:
            articles_summary.append({
                'title': analysis.title,
                'category': analysis.category,
                'impact_score': analysis.impact_score,
                'companies': analysis.companies,
                'technologies': analysis.technologies,
                'sentiment': analysis.sentiment
            })
        
        trend_prompt = f"""Analyze {len(analyses)} AI articles. Respond with ONLY valid JSON.

ARTICLES: {json.dumps(articles_summary[:5], indent=1)}

RESPONSE FORMAT (copy exactly):
{{
"key_trends": ["AI advancement", "Industry growth"],
"hot_companies": ["OpenAI", "Google"],
"emerging_technologies": ["LLM", "Robotics"],
"market_sentiment": "positive",
"investment_themes": ["AI infrastructure", "Enterprise AI"],
"notable_insights": ["Increased funding", "Technical breakthroughs"]
}}

Respond with ONLY the JSON above. No other text."""
        
        messages = [
            {"role": "system", "content": "You are a JSON API. Respond only with valid JSON. No explanations or additional text."},
            {"role": "user", "content": trend_prompt}
        ]
        
        print("📈 Generating trend analysis...")
        response = self._rate_limited_api_call(messages, max_tokens=1000)
        
        if not response:
            print("❌ Failed to generate trend analysis")
            return self._create_fallback_trends(analyses)
        
        try:
            # Clean the response
            cleaned_response = response.strip()
            
            # Try multiple JSON extraction methods
            trend_data = None
            
            # Method 1: Direct JSON parsing
            try:
                trend_data = json.loads(cleaned_response)
            except json.JSONDecodeError:
                pass
            
            # Method 2: Extract JSON from code blocks
            if not trend_data:
                json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned_response, re.DOTALL)
                if json_match:
                    try:
                        trend_data = json.loads(json_match.group(1).strip())
                    except json.JSONDecodeError:
                        pass
            
            # Method 3: Find JSON object in text
            if not trend_data:
                json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                if json_match:
                    try:
                        trend_data = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        pass
            
            if trend_data:
                print("✅ Trend analysis completed")
                return trend_data
            else:
                raise ValueError("Could not parse JSON from trend analysis response")
            
        except Exception as e:
            print(f"❌ Error parsing trend analysis response: {e}")
            print(f"Response was: {response[:200]}...")
            return self._create_fallback_trends(analyses)
    
    def _create_fallback_trends(self, analyses: List[ArticleAnalysis]) -> Dict:
        """Create basic trend analysis when AI analysis fails"""
        companies = []
        technologies = []
        categories = []
        
        for analysis in analyses:
            companies.extend(analysis.companies)
            technologies.extend(analysis.technologies)
            categories.append(analysis.category)
        
        # Count frequencies
        from collections import Counter
        company_counts = Counter(companies)
        tech_counts = Counter(technologies)
        category_counts = Counter(categories)
        
        return {
            "key_trends": ["AI advancement", "Industry consolidation", "Regulatory developments"],
            "hot_companies": list(company_counts.most_common(3)),
            "emerging_technologies": list(tech_counts.most_common(3)),
            "market_sentiment": "mixed",
            "investment_themes": ["AI infrastructure", "Enterprise AI", "AI safety"],
            "notable_insights": [
                f"Most common category: {category_counts.most_common(1)[0][0] if categories else 'N/A'}",
                f"Total articles analyzed: {len(analyses)}",
                "Analysis completed despite rate limiting"
            ]
        }

# Filter class for post-processing
class ArticleFilter:
    def __init__(self):
        pass
    
    def filter_by_quality(self, analyses: List[ArticleAnalysis]) -> List[ArticleAnalysis]:
        """Filter articles by quality metrics"""
        return [analysis for analysis in analyses 
                if analysis.confidence > 0.5 and analysis.impact_score > 3]
    
    def prioritize_by_relevance(self, analyses: List[ArticleAnalysis]) -> List[ArticleAnalysis]:
        """Sort articles by relevance score"""
        return sorted(analyses, key=lambda x: self.relevance_score(x), reverse=True)
    
    @staticmethod
    def relevance_score(analysis: ArticleAnalysis) -> float:
        """Calculate relevance score for an article"""
        score = analysis.impact_score * 0.4
        score += analysis.confidence * 0.3
        
        # Boost for certain categories
        category_boost = {
            'breakthrough': 2.0,
            'product_launch': 1.5,
            'funding': 1.3,
            'research': 1.2,
            'industry_news': 1.0,
            'regulatory': 1.1
        }
        score *= category_boost.get(analysis.category, 1.0)
        
        return score

# Test the enhanced summarizer
if __name__ == "__main__":
    # Test with API key from environment
    FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
    
    if not FIREWORKS_API_KEY:
        print("❌ FIREWORKS_API_KEY not found in environment")
        exit(1)
    
    print("🧪 Testing Enhanced Summarizer with Rate Limiting...")
    
    # Create test summarizer
    summarizer = EnhancedSummarizer(FIREWORKS_API_KEY)
    
    # Test article
    test_article = {
        'title': 'OpenAI Announces GPT-5 with Revolutionary Capabilities',
        'source': 'OpenAI',
        'link': 'https://openai.com/test',
        'content': 'OpenAI today announced GPT-5, a groundbreaking AI model that demonstrates unprecedented reasoning capabilities and can perform complex tasks across multiple domains. The model shows significant improvements in mathematical reasoning, coding abilities, and scientific analysis.'
    }
    
    # Test single article analysis
    analysis = summarizer.analyze_article(test_article)
    print(f"✅ Single article analysis: {analysis.title}")
    print(f"   Impact Score: {analysis.impact_score}")
    print(f"   Category: {analysis.category}")
    print(f"   Companies: {analysis.companies}")
    
    # Test batch analysis
    test_articles = [test_article] * 2  # Test with 2 articles
    analyses = summarizer.batch_analyze_articles(test_articles)
    print(f"✅ Batch analysis completed: {len(analyses)} articles")
    
    # Test trend analysis
    trends = summarizer.generate_trend_analysis(analyses)
    print(f"✅ Trend analysis: {trends.get('key_trends', ['No trends'])}")
    
    print("🎉 Enhanced summarizer test completed!") 