from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import secrets
import threading
from datetime import datetime
from pathlib import Path
import sys
import traceback
from dataclasses import dataclass
from typing import Optional

from rss_feeds import (
    ENHANCED_RSS_FEEDS, FEED_CATEGORIES,
    get_prioritized_feeds, fetch_rss_articles, extract_article_content,
    StateTracker,
)
from summarization import EnhancedSummarizer
from ui import EnhancedReportGenerator

# Configuration
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Thread-safe report status management
# ---------------------------------------------------------------------------

@dataclass
class ReportStatus:
    running: bool = False
    progress: str = ""
    error: Optional[str] = None
    last_report: Optional[str] = None
    start_time: Optional[datetime] = None
    articles_processed: int = 0


class ReportManager:
    def __init__(self):
        self._status = ReportStatus()
        self._lock = threading.Lock()

    def get_status(self) -> dict:
        with self._lock:
            return {
                'running': self._status.running,
                'progress': self._status.progress,
                'error': self._status.error,
                'last_report': self._status.last_report,
                'duration': (
                    (datetime.now() - self._status.start_time).total_seconds()
                    if self._status.start_time else 0
                ),
                'articles_processed': self._status.articles_processed,
            }

    def update_progress(self, progress: str, articles_processed: int = 0):
        with self._lock:
            self._status.progress = progress
            if articles_processed > 0:
                self._status.articles_processed = articles_processed

    def update_articles_processed(self, count: int):
        with self._lock:
            self._status.articles_processed = count

    def start_generation(self):
        with self._lock:
            self._status.running = True
            self._status.progress = "Starting report generation..."
            self._status.error = None
            self._status.last_report = None
            self._status.start_time = datetime.now()
            self._status.articles_processed = 0

    def finish_generation(
        self,
        report_filename: Optional[str] = None,
        error: Optional[str] = None,
    ):
        with self._lock:
            self._status.running = False
            if error:
                self._status.error = error
                self._status.progress = f"Error: {error}"
            elif report_filename:
                self._status.last_report = report_filename
                self._status.progress = "Report generation completed successfully!"
            else:
                self._status.progress = "No new articles found today."

    def is_running(self) -> bool:
        with self._lock:
            return self._status.running


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

report_manager = ReportManager()

# Check for API key (once)
_fireworks_key = os.getenv("FIREWORKS_API_KEY")
if not _fireworks_key:
    print("WARNING: FIREWORKS_API_KEY not set. Set it in your .env file.")
elif _fireworks_key == "your_fireworks_api_key_here":
    print("WARNING: FIREWORKS_API_KEY is set to placeholder. Update .env with your actual key.")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_available_sources() -> dict:
    """Get available RSS sources organized by category."""
    categorized: dict = {}
    for category, source_names in FEED_CATEGORIES.items():
        categorized[category] = {
            name: url
            for name, url in ENHANCED_RSS_FEEDS.items()
            if name in source_names
        }

    # Add uncategorized sources
    all_categorized = {name for names in FEED_CATEGORIES.values() for name in names}
    other = {
        name: url for name, url in ENHANCED_RSS_FEEDS.items()
        if name not in all_categorized
    }
    if other:
        categorized["other"] = other

    return categorized


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_enhanced_pipeline(selected_sources=None):
    """Run the news analysis pipeline.

    Pipeline flow:
        RSS feeds --> fetch --> deduplicate --> extract content
            --> AI analysis (Fireworks) --> trend synthesis --> PDF report
    """
    fireworks_key = os.getenv("FIREWORKS_API_KEY")
    if not fireworks_key or fireworks_key == "your_fireworks_api_key_here":
        raise Exception(
            "FIREWORKS_API_KEY not set. Please create a .env file with your API key."
        )

    summarizer = EnhancedSummarizer(fireworks_key)
    report_generator = EnhancedReportGenerator(REPORTS_DIR)
    state_tracker = StateTracker()

    # Step 1: Determine which feeds to use
    report_manager.update_progress("Setting up RSS feeds...")
    if selected_sources:
        all_sources = get_available_sources()
        selected_feeds = {
            name: url
            for category_sources in all_sources.values()
            for name, url in category_sources.items()
            if name in selected_sources
        }
        if not selected_feeds:
            raise Exception("No valid sources selected")
    else:
        selected_feeds = get_prioritized_feeds(15)

    # Step 2: Fetch articles
    report_manager.update_progress(
        f"Fetching articles from {len(selected_feeds)} sources..."
    )
    articles = fetch_rss_articles(selected_feeds)

    if not articles:
        report_manager.update_progress("No articles found from selected sources.")
        return None

    # Step 3: Filter new articles and cap to avoid long runs
    MAX_ARTICLES_PER_RUN = 25
    report_manager.update_progress("Filtering for new articles...")
    new_articles = state_tracker.filter_new_articles(articles)

    if not new_articles:
        report_manager.update_progress("No new articles to process.")
        return None

    if len(new_articles) > MAX_ARTICLES_PER_RUN:
        report_manager.update_progress(
            f"Found {len(new_articles)} new articles, processing top {MAX_ARTICLES_PER_RUN}..."
        )
        new_articles = new_articles[:MAX_ARTICLES_PER_RUN]

    # Step 4: Extract content
    report_manager.update_progress(
        f"Extracting content from {len(new_articles)} articles..."
    )
    articles_with_content = []
    for i, article in enumerate(new_articles):
        content = extract_article_content(article)
        if content:
            articles_with_content.append({**article, "content": content[:2000]})
        report_manager.update_progress(
            f"Extracting content: {i + 1}/{len(new_articles)} articles..."
        )

    if not articles_with_content:
        report_manager.update_progress("No articles with extractable content found.")
        return None

    # Step 5: AI analysis
    report_manager.update_progress(
        f"Analyzing {len(articles_with_content)} articles with AI..."
    )
    report_manager.update_articles_processed(len(articles_with_content))
    analyzed_articles = summarizer.batch_analyze_articles(articles_with_content)

    if not analyzed_articles:
        report_manager.update_progress("No articles passed analysis.")
        return None

    # Step 6: Trend analysis
    report_manager.update_progress("Generating trend analysis...")
    trend_analysis = summarizer.generate_trend_analysis(analyzed_articles)

    # Step 7: Generate report
    report_manager.update_progress("Generating report...")
    result = report_generator.generate_enhanced_report(analyzed_articles, trend_analysis)

    # Step 8: Mark articles as processed
    sent_links = [a.get("link", "") for a in new_articles if a.get("link")]
    if sent_links:
        state_tracker.mark_articles_sent(sent_links)

    return result


def run_report_generation(selected_sources=None):
    """Background function to run report generation."""
    try:
        report_manager.start_generation()
        result = run_enhanced_pipeline(selected_sources)

        if result and result.get("pdf_report"):
            report_manager.finish_generation(
                report_filename=Path(result["pdf_report"]).name
            )
        else:
            report_manager.finish_generation()

    except Exception as e:
        report_manager.finish_generation(error=str(e))
        print(f"Error in report generation: {e}")
        traceback.print_exc()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Main page."""
    available_sources = get_available_sources()
    status = report_manager.get_status()

    reports = []
    try:
        if REPORTS_DIR.exists():
            for report_file in REPORTS_DIR.glob("*.pdf"):
                reports.append({
                    "filename": report_file.name,
                    "created": datetime.fromtimestamp(
                        report_file.stat().st_mtime
                    ).strftime("%Y-%m-%d %H:%M"),
                    "size": f"{report_file.stat().st_size / 1024:.1f} KB",
                })
            reports.sort(key=lambda x: x["created"], reverse=True)
    except Exception as e:
        print(f"Error listing reports: {e}")

    return render_template(
        "index.html",
        available_sources=available_sources,
        status=status,
        reports=reports,
    )


@app.route("/api/sources")
def get_sources():
    """API endpoint to get available sources."""
    return jsonify(get_available_sources())


@app.route("/generate_report", methods=["POST"])
def generate_report():
    """Start report generation in background."""
    if report_manager.is_running():
        flash("Report generation is already in progress!", "warning")
        return redirect(url_for("index"))

    selected_sources = request.form.getlist("sources")

    thread = threading.Thread(
        target=run_report_generation, args=(selected_sources,)
    )
    thread.start()

    if selected_sources:
        flash(
            f"Report generation started with {len(selected_sources)} selected sources!",
            "info",
        )
    else:
        flash("Report generation started with default sources!", "info")

    return redirect(url_for("index"))


@app.route("/status")
def get_status():
    """Get current report generation status (for AJAX polling)."""
    return jsonify(report_manager.get_status())


@app.route("/download/<filename>")
def download_report(filename):
    """Download a specific report file."""
    try:
        filename = secure_filename(filename)
        file_path = REPORTS_DIR / filename
        if file_path.exists() and file_path.suffix == ".pdf":
            return send_file(file_path, as_attachment=True)
        else:
            flash("Report file not found!", "error")
            return redirect(url_for("index"))
    except Exception as e:
        flash(f"Error downloading file: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/delete/<filename>", methods=["POST"])
def delete_report(filename):
    """Delete a specific report file."""
    try:
        filename = secure_filename(filename)
        file_path = REPORTS_DIR / filename
        if file_path.exists() and file_path.suffix == ".pdf":
            file_path.unlink()
            flash(f"Report {filename} deleted successfully!", "success")
        else:
            flash("Report file not found!", "error")
    except Exception as e:
        flash(f"Error deleting file: {str(e)}", "error")

    return redirect(url_for("index"))


@app.route("/health")
def health():
    """Health check endpoint for deployment monitoring."""
    api_key_set = bool(os.getenv("FIREWORKS_API_KEY"))
    return jsonify({
        "status": "healthy",
        "api_key_configured": api_key_set,
        "reports_dir_exists": REPORTS_DIR.exists(),
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/debug/test-api")
def debug_test_api():
    """Test the Fireworks API with a single call to diagnose issues."""
    fireworks_key = os.getenv("FIREWORKS_API_KEY")
    if not fireworks_key:
        return jsonify({"error": "FIREWORKS_API_KEY not set"}), 500

    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=fireworks_key,
        )
        model_id = "accounts/fireworks/models/llama-v3p1-8b-instruct"
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "user", "content": "Reply with exactly: {\"test\": \"ok\"}"}
            ],
            temperature=0.0,
            max_tokens=50,
        )
        content = response.choices[0].message.content.strip()
        return jsonify({
            "status": "ok",
            "model": model_id,
            "response": content,
            "api_key_prefix": fireworks_key[:8] + "...",
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)[:500],
            "model": "llama-v3p1-8b-instruct",
            "api_key_prefix": fireworks_key[:8] + "...",
        }), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Starting AI News Digest...")

    fireworks_key = os.getenv("FIREWORKS_API_KEY")
    if not fireworks_key:
        print("FIREWORKS_API_KEY not found. Create a .env file with: FIREWORKS_API_KEY=your_key")
    elif fireworks_key == "your_fireworks_api_key_here":
        print("FIREWORKS_API_KEY is set to placeholder. Update .env with your actual key.")

    app.run(
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
        host="0.0.0.0",
        port=8080,
    )
