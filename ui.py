# Report generation and PDF output

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# PDF generation imports
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Enhanced configuration and features
ENHANCED_FEATURES = {
    'categories': [
        'breakthrough', 'product', 'funding', 'partnership', 
        'research', 'regulation', 'acquisition', 'general'
    ],
    'impact_levels': {
        'high': {'min_score': 8, 'color': '#e74c3c', 'label': 'High Impact'},
        'medium': {'min_score': 5, 'color': '#f39c12', 'label': 'Medium Impact'},
        'low': {'min_score': 1, 'color': '#2ecc71', 'label': 'Low Impact'}
    },
    'sources': [
        'OpenAI', 'Hugging Face', 'Anthropic', 'DeepMind', 'Google AI',
        'Microsoft AI', 'NVIDIA', 'Meta AI', 'VentureBeat AI', 'TechCrunch AI'
    ],
    'timeframes': [
        {'label': 'Last 24 hours', 'hours': 24},
        {'label': 'Last 3 days', 'hours': 72},
        {'label': 'Last week', 'hours': 168},
        {'label': 'Last month', 'hours': 720}
    ]
}

class EnhancedReportGenerator:
    """Enhanced report generation with multiple formats and insights"""
    
    def __init__(self, reports_dir: Path):
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_enhanced_report(self, analyses: List, trend_analysis: Dict) -> Dict:
        """Generate comprehensive report with trends and insights"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate the main PDF report (compatible with existing system)
        pdf_filename = f"ai_news_digest_{timestamp}.pdf"
        pdf_path = self._generate_main_pdf_report(analyses, trend_analysis, pdf_filename)
        
        # Generate additional reports
        csv_path = self._generate_enhanced_csv(analyses, timestamp)
        trends_path = self._generate_trends_json(trend_analysis, timestamp)
        
        return {
            'pdf_report': pdf_path,  # Main report for compatibility
            'csv_report': csv_path,
            'trends_report': trends_path,
            'articles_count': len(analyses),
            'timestamp': timestamp,
            'summary': {
                'total_articles': len(analyses),
                'high_impact_articles': len([a for a in analyses if getattr(a, 'impact_score', 5) >= 8]),
                'avg_impact_score': sum(getattr(a, 'impact_score', 5) for a in analyses) / len(analyses) if analyses else 0,
                'top_categories': self._get_top_categories(analyses),
                'key_trends': trend_analysis.get('key_trends', [])
            }
        }
    
    def _generate_executive_pdf(self, analyses: List, trend_analysis: Dict, timestamp: str) -> str:
        """Generate executive summary PDF"""
        # Implementation would go here
        filename = f"executive_summary_{timestamp}.pdf"
        return str(self.reports_dir / filename)
    
    def _generate_detailed_pdf(self, analyses: List, trend_analysis: Dict, timestamp: str) -> str:
        """Generate detailed analysis PDF"""
        # Implementation would go here
        filename = f"detailed_analysis_{timestamp}.pdf"
        return str(self.reports_dir / filename)
    
    def _generate_main_pdf_report(self, analyses: List, trend_analysis: Dict, filename: str) -> str:
        """Generate the main PDF report with enhanced analysis"""
        
        if not PDF_AVAILABLE:
            print("❌ ReportLab not installed. Cannot generate PDF.")
            return None
        
        file_path = self.reports_dir / filename
        
        print(f"📄 Generating enhanced PDF report: {filename}")
        
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                str(file_path),
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
                spaceAfter=20,
                alignment=1
            )
            
            trend_title_style = ParagraphStyle(
                'TrendTitle',
                parent=styles['Heading2'],
                fontSize=18,
                textColor=HexColor('#2c5aa0'),
                spaceBefore=20,
                spaceAfter=15
            )
            
            article_title_style = ParagraphStyle(
                'ArticleTitle',
                parent=styles['Heading3'],
                fontSize=14,
                textColor=HexColor('#2c5aa0'),
                spaceBefore=15,
                spaceAfter=8
            )
            
            analysis_style = ParagraphStyle(
                'Analysis',
                parent=styles['Normal'],
                fontSize=10,
                textColor=HexColor('#333333'),
                spaceAfter=8,
                leftIndent=20
            )
            
            # Build document content
            story = []
            
            # Title and metadata
            story.append(Paragraph("🚀 Enhanced AI News & Research Digest", title_style))
            story.append(Paragraph(
                f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
                subtitle_style
            ))
            story.append(Paragraph(
                f"Total Articles: {len(analyses)} | Enhanced Analysis with Impact Scoring",
                subtitle_style
            ))
            
            story.append(Spacer(1, 20))
            
            # Executive Summary
            if trend_analysis:
                story.append(Paragraph("📈 Executive Summary & Market Trends", trend_title_style))
                
                # Key trends
                if trend_analysis.get('key_trends'):
                    story.append(Paragraph("<b>Key Market Trends:</b>", analysis_style))
                    for trend in trend_analysis.get('key_trends', [])[:5]:
                        story.append(Paragraph(f"• {trend}", analysis_style))
                    story.append(Spacer(1, 10))
                
                # Hot companies
                if trend_analysis.get('hot_companies'):
                    story.append(Paragraph("<b>Most Active Companies:</b>", analysis_style))
                    companies = trend_analysis.get('hot_companies', [])
                    if isinstance(companies[0], list):  # Handle Counter format
                        company_text = ", ".join([f"{comp[0]} ({comp[1]})" for comp in companies[:5]])
                    else:
                        company_text = ", ".join(companies[:5])
                    story.append(Paragraph(company_text, analysis_style))
                    story.append(Spacer(1, 10))
                
                # Market sentiment
                sentiment = trend_analysis.get('market_sentiment', 'mixed')
                story.append(Paragraph(f"<b>Market Sentiment:</b> {sentiment.title()}", analysis_style))
                story.append(Spacer(1, 20))
            
            # Articles section
            story.append(Paragraph("📰 Article Analysis", trend_title_style))
            
            # Sort articles by impact score
            sorted_analyses = sorted(analyses, 
                                   key=lambda x: getattr(x, 'impact_score', 5), 
                                   reverse=True)
            
            for i, analysis in enumerate(sorted_analyses):
                # Article title with impact score
                impact_score = getattr(analysis, 'impact_score', 5)
                category = getattr(analysis, 'category', 'general')
                title = getattr(analysis, 'title', 'Unknown Title')
                
                impact_emoji = "🔥" if impact_score >= 8 else "⚡" if impact_score >= 6 else "📊"
                
                story.append(Paragraph(
                    f"{impact_emoji} {title}",
                    article_title_style
                ))
                
                # Metadata
                source = getattr(analysis, 'source', 'Unknown Source')
                story.append(Paragraph(
                    f"<b>Source:</b> {source} | <b>Impact Score:</b> {impact_score}/10 | <b>Category:</b> {category.title()}",
                    analysis_style
                ))
                
                # Summary
                summary = getattr(analysis, 'summary', 'Summary not available')
                story.append(Paragraph(f"<b>Summary:</b> {summary}", analysis_style))
                
                # Enhanced insights
                market_impl = getattr(analysis, 'market_implications', None)
                if market_impl and market_impl != 'Analysis not available due to rate limiting':
                    story.append(Paragraph(f"<b>Market Impact:</b> {market_impl}", analysis_style))
                
                investment_angle = getattr(analysis, 'investment_angle', None)
                if investment_angle and investment_angle != 'Analysis not available due to rate limiting':
                    story.append(Paragraph(f"<b>Investment Angle:</b> {investment_angle}", analysis_style))
                
                # Companies and technologies
                companies = getattr(analysis, 'companies', [])
                if companies:
                    story.append(Paragraph(f"<b>Key Companies:</b> {', '.join(companies)}", analysis_style))
                
                technologies = getattr(analysis, 'technologies', [])
                if technologies:
                    story.append(Paragraph(f"<b>Technologies:</b> {', '.join(technologies)}", analysis_style))
                
                # Link
                link = getattr(analysis, 'link', '')
                if link:
                    story.append(Paragraph(
                        f'<b>Read more:</b> <link href="{link}" color="blue">{link}</link>',
                        analysis_style
                    ))
                
                # Add separator except for last article
                if i < len(sorted_analyses) - 1:
                    story.append(Spacer(1, 15))
                    story.append(Paragraph("_" * 80, styles['Normal']))
                    story.append(Spacer(1, 15))
            
            # Footer
            story.append(Spacer(1, 30))
            story.append(Paragraph(
                "Generated by Enhanced AI News Aggregator - Strategic Intelligence Platform",
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
            
            print(f"✅ Enhanced PDF report generated successfully: {filename}")
            return str(file_path)
            
        except Exception as e:
            print(f"❌ Error generating enhanced PDF: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_enhanced_csv(self, analyses: List, timestamp: str) -> str:
        """Generate enhanced CSV with all analysis data"""
        # Implementation would go here
        filename = f"detailed_data_{timestamp}.csv"
        return str(self.reports_dir / filename)
    
    def _generate_trends_json(self, trend_analysis: Dict, timestamp: str) -> str:
        """Generate trends analysis JSON"""
        filename = f"trends_{timestamp}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'analysis': trend_analysis
            }, f, indent=2)
        
        return str(filepath)
    
    def _get_top_categories(self, analyses: List) -> List[Dict]:
        """Get top categories by frequency"""
        category_counts = {}
        for analysis in analyses:
            category = getattr(analysis, 'category', 'general')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return [
            {'category': cat, 'count': count}
            for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        ]

