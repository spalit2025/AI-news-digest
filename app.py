from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
import os
import json
import threading
import time
from datetime import datetime
from pathlib import Path
import sys
import traceback

# Enhanced imports
from rss_feeds import RSSFeedValidator, ENHANCED_RSS_FEEDS, FEED_CATEGORIES
from summarization import EnhancedSummarizer
from ui import EnhancedReportGenerator

# Enhanced mode is now always enabled
ENHANCED_MODE = True
print("✅ Enhanced modules loaded successfully")

# Create reports directory
try:
    from legacy.optimized_ai_news import REPORTS_DIR
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
except ImportError:
    REPORTS_DIR = "reports"
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

# Check for API key
if not os.environ.get('FIREWORKS_API_KEY'):
    print("⚠️ FIREWORKS_API_KEY not set - some features may not work")
    print("   Please set it in your environment or .env file")
else:
    print("✅ FIREWORKS_API_KEY found in environment")

# Check enhanced mode
if ENHANCED_MODE:
    print("🚀 Enhanced mode enabled - will use improved RSS feeds and AI analysis")
else:
    print("📰 Basic mode - using standard RSS feeds")

# Import pipeline functions based on mode
if ENHANCED_MODE:
    print("🔧 Checking environment setup...")
    
    # Check for API key
    if not os.environ.get('FIREWORKS_API_KEY'):
        print("⚠️ FIREWORKS_API_KEY not set - some features may not work")
        print("   Please set it in your environment or .env file")
    else:
        print("✅ FIREWORKS_API_KEY found in environment")
    
    try:
        from legacy.optimized_ai_news import fetch_rss_articles, smart_content_extraction, ArticleCache, StateTracker
        from rss_feeds import get_prioritized_feeds, validate_and_fix_feeds
        from summarization import EnhancedSummarizer
        from ui import EnhancedReportGenerator
        print("✅ Enhanced modules loaded successfully")
    except ImportError as e:
        print(f"❌ Failed to import enhanced modules: {e}")
        ENHANCED_MODE = False
else:
    try:
        from legacy.optimized_ai_news import run_pipeline_optimized
        print("✅ Legacy pipeline loaded")
    except ImportError as e:
        print(f"❌ Failed to import legacy pipeline: {e}")
        sys.exit(1)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Global variable to track report generation status
report_status = {
    'running': False,
    'progress': '',
    'error': None,
    'last_report': None,
    'enhanced_mode': ENHANCED_MODE
}

def get_available_sources():
    """Get available RSS sources organized by category"""
    try:
        from rss_feeds import get_prioritized_feeds, validate_and_fix_feeds
        from legacy.optimized_ai_news import fetch_rss_articles, smart_content_extraction, ArticleCache, StateTracker
        import json
        
        # Enhanced mode - organize sources by category
        categorized_sources = {}
        for category, source_names in FEED_CATEGORIES.items():
            categorized_sources[category] = {}
            for source_name in source_names:
                if source_name in ENHANCED_RSS_FEEDS:
                    categorized_sources[category][source_name] = ENHANCED_RSS_FEEDS[source_name]
        
        # Add uncategorized sources
        categorized_sources["other"] = {}
        for source_name, url in ENHANCED_RSS_FEEDS.items():
            # Check if source is not in any category
            in_category = False
            for category_sources in FEED_CATEGORIES.values():
                if source_name in category_sources:
                    in_category = True
                    break
            if not in_category:
                categorized_sources["other"][source_name] = url
        
        return categorized_sources
    except ImportError as e:
        print(f"⚠️ Enhanced modules not available: {e}")
        return {
            "basic": {
                "NVIDIA AI Blog": "https://blogs.nvidia.com/blog/category/ai/feed/",
                "Hugging Face": "https://huggingface.co/blog/feed.xml",
                "Google AI": "https://ai.googleblog.com/feeds/posts/default",
                "OpenAI": "https://openai.com/news/rss.xml",
                "Meta AI": "https://about.fb.com/news/category/ai/feed/",
                "Anthropic": "https://www.anthropic.com/news/rss.xml",
                "Uber AI": "https://www.uber.com/blog/engineering/ai/feed/"
            }
        }

def run_enhanced_pipeline(selected_sources=None):
    """Run the enhanced pipeline with better RSS feeds and summarization"""
    try:
        # Import required modules
        from rss_feeds import get_prioritized_feeds, validate_and_fix_feeds
        from legacy.optimized_ai_news import fetch_rss_articles, smart_content_extraction, ArticleCache, StateTracker
        import json
        
        # Initialize components
        cache = ArticleCache()
        state_tracker = StateTracker()
        
        # Get API key
        fireworks_key = os.getenv("FIREWORKS_API_KEY")
        if not fireworks_key:
            raise Exception("FIREWORKS_API_KEY not found in environment")
        
        summarizer = EnhancedSummarizer(fireworks_key)
        report_generator = EnhancedReportGenerator(REPORTS_DIR)
        
        # Step 1: Get RSS feeds based on selection
        report_status['progress'] = 'Setting up RSS feeds...'
        
        if selected_sources:
            # Use selected sources
            selected_feeds = {}
            all_sources = get_available_sources()
            for category, sources in all_sources.items():
                for source_name, url in sources.items():
                    if source_name in selected_sources:
                        selected_feeds[source_name] = url
            
            if not selected_feeds:
                raise Exception("No valid sources selected")
        else:
            # Use default enhanced feeds
            selected_feeds = get_prioritized_feeds(15)
        
        # Temporarily replace the RSS feeds in the optimized script
        import legacy.optimized_ai_news as optimized_ai_news
        original_feeds = optimized_ai_news.RSS_FEEDS
        optimized_ai_news.RSS_FEEDS = selected_feeds
        
        # Step 2: Fetch articles using selected feeds
        report_status['progress'] = f'Fetching articles from {len(selected_feeds)} selected sources...'
        articles = fetch_rss_articles()
        
        # Restore original feeds
        optimized_ai_news.RSS_FEEDS = original_feeds
        
        if not articles:
            report_status['progress'] = 'No new articles found from selected sources.'
            return None
        
        # Step 3: Filter new articles
        report_status['progress'] = 'Filtering for new articles...'
        new_articles = state_tracker.filter_new_articles(articles)
        
        if not new_articles:
            report_status['progress'] = 'No new articles to process.'
            return None
        
        # Step 4: Extract content
        report_status['progress'] = f'Extracting content from {len(new_articles)} articles...'
        articles_with_content = []
        
        for article in new_articles:
            content = smart_content_extraction(article)
            if content:
                articles_with_content.append({
                    **article,
                    'content': content[:2000]  # Limit content length
                })
        
        if not articles_with_content:
            report_status['progress'] = 'No articles with extractable content found.'
            return None
        
        # Step 5: Enhanced summarization with impact scoring
        report_status['progress'] = f'Analyzing {len(articles_with_content)} articles with enhanced AI...'
        analyzed_articles = summarizer.batch_analyze_articles(articles_with_content)
        
        if not analyzed_articles:
            report_status['progress'] = 'No articles passed enhanced analysis.'
            return None
        
        # Step 6: Generate trend analysis
        report_status['progress'] = 'Generating trend analysis...'
        trend_analysis = summarizer.generate_trend_analysis(analyzed_articles)
        
        # Step 7: Generate enhanced report
        report_status['progress'] = 'Generating enhanced report...'
        result = report_generator.generate_enhanced_report(analyzed_articles, trend_analysis)
        
        # Step 8: Mark articles as sent
        sent_urls = [article.title for article in analyzed_articles if hasattr(article, 'title')]
        if sent_urls:
            state_tracker.mark_articles_sent(sent_urls)
        
        return result
        
    except Exception as e:
        raise Exception(f"Enhanced pipeline failed: {str(e)}")

@app.route('/')
def index():
    """Main page"""
    available_sources = get_available_sources()
    return render_template('index.html', 
                         available_sources=available_sources,
                         enhanced_mode=ENHANCED_MODE)

@app.route('/api/sources')
def get_sources():
    """API endpoint to get available sources"""
    return jsonify(get_available_sources())

@app.route('/generate_report', methods=['POST'])
def generate_report():
    """Start report generation in background"""
    global report_status
    
    if report_status['running']:
        flash('Report generation is already in progress!', 'warning')
        return redirect(url_for('index'))
    
    # Get selected sources from form
    selected_sources = request.form.getlist('sources')
    
    # Start report generation in background thread
    thread = threading.Thread(target=run_report_generation, args=(selected_sources,))
    thread.start()
    
    if selected_sources:
        flash(f'Report generation started with {len(selected_sources)} selected sources!', 'info')
    else:
        flash('Report generation started with default sources!', 'info')
    
    return redirect(url_for('index'))

@app.route('/status')
def get_status():
    """Get current report generation status (for AJAX polling)"""
    return jsonify(report_status)

@app.route('/download/<filename>')
def download_report(filename):
    """Download a specific report file"""
    try:
        file_path = REPORTS_DIR / filename
        if file_path.exists() and file_path.suffix == '.pdf':
            return send_file(file_path, as_attachment=True)
        else:
            flash('Report file not found!', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/delete/<filename>')
def delete_report(filename):
    """Delete a specific report file"""
    try:
        file_path = REPORTS_DIR / filename
        if file_path.exists() and file_path.suffix == '.pdf':
            file_path.unlink()
            flash(f'Report {filename} deleted successfully!', 'success')
        else:
            flash('Report file not found!', 'error')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')
    
    return redirect(url_for('index'))

def run_report_generation(selected_sources=None):
    """Background function to run report generation"""
    global report_status
    
    try:
        report_status['running'] = True
        report_status['progress'] = 'Starting report generation...'
        report_status['error'] = None
        report_status['last_report'] = None
        
        # Check for API key first
        fireworks_key = os.getenv("FIREWORKS_API_KEY")
        if not fireworks_key or fireworks_key == "your_fireworks_api_key_here":
            raise Exception("FIREWORKS_API_KEY not set! Please create a .env file with your API key.")
        
        # Capture stdout to show progress
        class ProgressCapture:
            def __init__(self):
                self.messages = []
            
            def write(self, text):
                if text.strip():
                    self.messages.append(text.strip())
                    report_status['progress'] = text.strip()
                # Also write to original stdout
                sys.__stdout__.write(text)
            
            def flush(self):
                sys.__stdout__.flush()
        
        # Redirect stdout to capture progress
        old_stdout = sys.stdout
        progress_capture = ProgressCapture()
        sys.stdout = progress_capture
        
        # Run the appropriate pipeline
        if ENHANCED_MODE:
            print("🚀 Running ENHANCED AI news pipeline...")
            result = run_enhanced_pipeline(selected_sources)
        else:
            print("🚀 Running basic optimized pipeline...")
            from legacy.optimized_ai_news import run_pipeline_optimized
            result = run_pipeline_optimized()
        
        # Restore stdout
        sys.stdout = old_stdout
        
        if result and result.get('pdf_report'):
            report_status['progress'] = 'Report generation completed successfully!'
            report_status['last_report'] = Path(result['pdf_report']).name
        else:
            report_status['progress'] = 'No new articles found today.'
            
    except Exception as e:
        report_status['error'] = str(e)
        report_status['progress'] = f'Error: {str(e)}'
        print(f"Error in report generation: {e}")
        traceback.print_exc()
    finally:
        report_status['running'] = False

if __name__ == '__main__':
    # Ensure reports directory exists
    REPORTS_DIR.mkdir(exist_ok=True)
    
    # Check environment setup
    print("🔧 Checking environment setup...")
    fireworks_key = os.getenv("FIREWORKS_API_KEY")
    if not fireworks_key:
        print("❌ FIREWORKS_API_KEY not found in environment")
        print("📝 Create a .env file with: FIREWORKS_API_KEY=your_actual_api_key")
    elif fireworks_key == "your_fireworks_api_key_here":
        print("❌ FIREWORKS_API_KEY is set to placeholder value")
        print("📝 Update .env file with your actual Fireworks API key")
    else:
        print("✅ FIREWORKS_API_KEY found in environment")
    
    if ENHANCED_MODE:
        print("🚀 Enhanced mode enabled - will use improved RSS feeds and AI analysis")
    else:
        print("⚠️ Running in basic mode - enhanced features not available")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=8080) 