# AI News Digest Web Application

A comprehensive AI-powered news aggregation and analysis tool with a modern web interface. This application collects AI/ML news from multiple sources, provides intelligent summaries with impact scoring, and generates professional reports.

## 🚀 Features

- **Enhanced RSS Feeds**: 19+ curated AI/ML sources with health monitoring
- **AI-Powered Analysis**: Multi-dimensional impact scoring, categorization, and market analysis
- **Modern Web Interface**: Real-time progress tracking and responsive design
- **Professional Reports**: PDF generation with executive summaries and trend analysis
- **Intelligent Caching**: Efficient processing with duplicate detection
- **Rate Limiting Protection**: Robust API call management with retry logic

## 📋 Requirements

- Python 3.8+
- Fireworks AI API key (for AI analysis)
- Dependencies listed in `requirements.txt`

## 🛠️ Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd AI-news-digest
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```
FIREWORKS_API_KEY=your_fireworks_api_key_here
```

### 4. Run the Application
```bash
python app.py
```


## 📁 Project Structure

```
AI-news-digest/
├── app.py                      # Flask web application
├── enhanced_rss_feeds.py       # Enhanced RSS feed management
├── enhanced_summarization.py   # AI-powered analysis and summarization
├── enhanced_ui.py              # Enhanced UI report generation
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── templates/
│   └── index.html             # Web interface template
├── static/
│   ├── css/
│   │   └── style.css          # Application styling
│   └── js/
│       └── script.js          # Frontend functionality
├── reports/                   # Generated reports (ignored by git)
├── legacy/                    # Legacy files and documentation
└── README.md                  # This file
```

## 🔧 Usage

### Web Interface
1. Open `http://localhost:8080` in your browser
2. Click "Generate Report" to start the analysis
3. Monitor real-time progress updates
4. Download generated PDF reports from the interface

### Features Available:
- **Impact Scoring**: Articles rated 1-10 based on significance
- **Categorization**: Automatic classification (research, product, funding, etc.)
- **Market Analysis**: Business implications and investment insights
- **Trend Analysis**: Cross-article patterns and emerging themes
- **Executive Summaries**: High-level overviews for decision makers

## 📊 Data Sources

The application monitors 19+ AI/ML sources including:
- DeepMind Research
- OpenAI Blog
- Anthropic News
- Hugging Face Blog
- NVIDIA AI Blog
- Google AI Blog
- Meta AI Research
- And many more...

## 🔒 Security & Privacy

- API keys are stored locally in `.env` file
- No data is sent to external services except for AI analysis
- Generated reports are stored locally
- Cache files help minimize API usage

## 📈 Performance Features

- **Intelligent Caching**: Avoids re-processing articles
- **Rate Limiting**: Prevents API quota exhaustion
- **Batch Processing**: Efficient API usage
- **Health Monitoring**: RSS feed reliability tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔧 Troubleshooting

### Common Issues:

1. **Port 8080 in use**: Change port in `app.py` or stop conflicting service
2. **API Key errors**: Ensure `.env` file is properly configured
3. **PDF generation fails**: Check `reportlab` installation
4. **Rate limiting**: Wait between report generations


**Note**: This application uses AI services that may incur costs. Monitor your API usage accordingly.