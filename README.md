# Web Crawler & Reporting Platform

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Status](https://img.shields.io/badge/status-production--ready-green)

A **production-ready web crawler and reporting platform** with **social media support**, **intelligent NLP keyword extraction**, and **advanced blocking detection**. Built for Lab 2 and Lab 3 requirements with professional-grade architecture.

## 🚀 Features

### Core Crawling
- **Multi-format Support**: HTML, RSS/XML, PDF, TXT
- **Social Media Sources**: Twitter/X (via Nitter), Reddit (JSON API), YouTube (RSS), LinkedIn (public pages)
- **Intelligent Scheduling**: Per-source cron-based automation with APScheduler
- **Politeness**: Robots.txt compliance, rate limiting (requests/minute), retry policies
- **Blocking Detection**: HTTP 403/429/503, CAPTCHA recognition, IP ban detection with auto-pause

### Advanced NLP Keywords
- **No Stopwords**: Multi-language stopword filtering (English + French + custom)
- **Lemmatization**: Word normalization using NLTK
- **TF-IDF Scoring**: Statistical keyword relevance
- **RAKE Algorithm**: Rapid automatic keyword extraction
- **N-grams**: Bigrams and trigrams for phrase detection
- **Frequency Filtering**: Minimum occurrence thresholds

**No more "the", "is", "wa", "and" in your keyword lists!**

### Modern Dashboard
- **5 Interactive Tabs**: Sources, Social Media, Monitoring, Search, Analytics, Reports
- **Real-time Status**: RUNNING, COMPLETED, PAUSED, BLOCKED (with animated indicators)
- **Advanced Analytics**: 4 Chart.js visualizations including Web vs Social Media comparison
- **Export Capabilities**: CSV and PDF reports with intelligent keyword analysis
- **Responsive Design**: Dark theme with glassmorphism effects

### Production Features
- **MongoDB Atlas Ready**: Full document storage with text indexing
- **RESTful API**: 20+ endpoints with FastAPI
- **Comprehensive Testing**: Unit and integration tests for parsers, NLP, and blocking
- **Strict Configuration**: Rate limit and max_hits enforcement
- **Professional Logging**: Structured logging with rotating file handlers

## 📋 Requirements

### System Requirements
- **Python**: 3.10 or higher
- **MongoDB**: 4.4+ (local or Atlas)
- **Windows**: Tested on Windows 10/11
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 500MB for application + space for crawled data

### Python Dependencies
Core dependencies are listed in `requirements.txt`:
- `fastapi` - REST API framework
- `uvicorn` - ASGI server
- `pymongo` - MongoDB driver
- `beautifulsoup4` - HTML parsing
- `feedparser` - RSS/XML parsing
- `PyPDF2` - PDF text extraction
- `APScheduler` - Cron scheduling
- `nltk` - Natural language processing
- `scikit-learn` - TF-IDF vectorization
- `rake-nltk` - RAKE keyword extraction
- `reportlab` - PDF report generation

## 🔧 Installation

### 1. Clone or Download Project
```bash
cd "Web Analytics Project"
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

**Note**: This will install ~20 packages including NLP libraries. Installation may take 2-5 minutes.

### 3. Download NLTK Data (First Run Only)
The application will automatically download required NLTK data on first run, but you can pre-download:
```python
import nltk
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
```

### 4. Configure MongoDB

#### Option A: Local MongoDB
1. Install MongoDB Community Edition from https://www.mongodb.com/try/download/community
2. Start MongoDB service:
   ```bash
   net start MongoDB
   ```
3. Verify connection: `mongo` or `mongosh`

#### Option B: MongoDB Atlas (Cloud)
1. Create free account at https://www.mongodb.com/cloud/atlas
2. Create cluster and get connection string
3. Update `.env` file with your URI

### 5. Configure Environment
Copy `.env.example` to `.env` and update:
```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=web_crawler

# Crawler Configuration
CRAWLER_USER_AGENT=WebCrawlerBot/1.0
CRAWLER_DELAY=1.0
MAX_WORKERS=5
REQUEST_TIMEOUT=30
MAX_RETRIES=3

# Logging
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8000
```

## 🚀 Usage

### Starting the Application
```bash
python main.py
```

Expected output:
```
2025-12-28 09:00:00 - web_crawler - INFO - Starting Web Crawler & Reporting Platform...
2025-12-28 09:00:00 - web_crawler - INFO - API will be available at http://0.0.0.0:8000
INFO:     Started server process [12345]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Accessing the Dashboard
Open your browser and navigate to:
```
http://localhost:8000/
```

### Adding Sources

#### Web Source
1. Click "+ Add Web Source" on Sources tab
2. Fill in:
   - **Name**: "Tech News"
   - **URL**: https://example.com/blog
   - **Content Type**: HTML
   - **Crawl Frequency**: `0 8 * * *` (daily at 8 AM)
   - **Max Pages**: 50
   - **Rate Limit**: 30 req/min
3. Click "Add Source"

#### Social Media Source
1. Navigate to "Social Media" tab
2. Click on platform card (Twitter, Reddit, YouTube, LinkedIn)
3. Fill in URL:
   - **Twitter**: `@username` or `https://twitter.com/username`
   - **Reddit**: `r/python` or `https://reddit.com/r/python`
   - **YouTube**: Channel URL with `/channel/` or playlist URL
   - **LinkedIn**: `https://linkedin.com/company/name` (public pages only)
4. Configure crawl settings
5. Click "Add Source"

**Note**: Twitter uses Nitter RSS (no API key needed), Reddit uses public JSON API, YouTube uses RSS feeds.

### Starting a Crawl
1. Navigate to Sources or Social Media tab
2. Find your source in the table
3. Click "▶ Start" button
4. Monitor progress in "Monitoring" tab
5. Check for BLOCKED status if crawl stops (rate limiting detected)

### Searching Documents
1. Navigate to "Search" tab
2. Enter keywords: `Python machine learning`
3. Select operator: `AND` (all keywords) or `OR` (any keyword)
4. Filter by content type if desired
5. Click "Search"
6. Results show with keyword highlighting and relevance scores

### Viewing Analytics
Navigate to "Analytics" tab to see 4 charts:
1. **Documents per Source**: Bar chart showing collection volume
2. **Crawl Activity Over Time**: Line chart showing 30-day activity
3. **Web vs Social Media**: Doughnut chart comparing platform distribution
4. **Top Keywords**: Horizontal bar chart with intelligent NLP keywords

### Generating Reports
Navigate to "Reports" tab and choose:
- **Keyword Frequency Report**: Top keywords with intelligent extraction (CSV/PDF)
- **Source Summary Report**: Document counts per source (CSV/PDF)
- **Documents Export**: All collected documents (CSV only)

## 🤖 Social Media Sources

### Twitter/X via Nitter
- **Format**: `@username` or full URL
- **Method**: Nitter RSS feeds (fallback instances: nitter.net, nitter.poast.org, nitter.privacydev.net)
- **No API Key Required**
- **Rate Limit**: Respect instance limits (30 req/min recommended)
- **Data**: Tweets, author, timestamps

### Reddit
- **Format**: `r/subreddit` or `https://reddit.com/r/subreddit`
- **Method**: Public JSON API
- **No Authentication Required**
- **Rate Limit**: 60 requests/minute (Reddit's limit)
- **Data**: Posts, titles, selftext, scores, comments count, authors

### YouTube
- **Format**: Channel URL or playlist URL
- **Method**: YouTube RSS feeds
- **No API Key Required**
- **Data**: Video titles, descriptions, publish dates, authors

### LinkedIn
- **Format**: `https://linkedin.com/company/slug`
- **Method**: Public page scraping
- **Limitations**: Requires public pages, no authentication support
- **Data**: Company name, description, posts (limited)

## 🧠 Intelligent Keywords

### How It Works
The keyword extraction uses **multiple NLP techniques** combined:

1. **Stopwords Removal**: 500+ stopwords (English, French, noise terms)
2. **Lemmatization**: "running" → "run", "better" → "good"
3. **TF-IDF**: Statistical term importance across documents
4. **RAKE**: Phrase extraction for multi-word keywords
5. **N-grams**: Bigrams ("machine learning") and trigrams
6. **Frequency Filtering**: Minimum occurrence thresholds

### Configuration
In code (`src/processing/intelligent_keywords.py`):
```python
# Add custom stopwords
self.stopwords.update({'custom', 'noise', 'words'})

# Adjust minimum word length
def _is_valid_word(self, word: str, min_length: int = 3)

# Change scoring weights
keyword_scores[word] += freq * 1.0  # Adjust multiplier
```

### API Usage
```python
from src.processing.intelligent_keywords import intelligent_extractor

text = "Your document text here..."
keywords = intelligent_extractor.get_best_keywords(text, top_n=20)
```

## 📡 API Endpoints

### Sources
- `POST /api/sources/` - Create source
- `GET /api/sources/` - List all sources
- `GET /api/sources/{id}` - Get source details
- `PUT /api/sources/{id}` - Update source
- `DELETE /api/sources/{id}` - Delete source

### Crawler
- `POST /api/crawler/start/{id}` - Start crawl
- `POST /api/crawler/stop/{id}` - Pause crawl
- `POST /api/crawler/resume/{id}` - Resume crawl
- `GET /api/crawler/status/{id}` - Get crawl status
- `GET /api/crawler/stats` - Global statistics
- `GET /api/crawler/jobs` - List scheduled jobs

### Search
- `GET /api/search/?q=keywords&operator=AND` - Search documents
- `GET /api/search/suggestions?q=prefix` - Keyword suggestions (placeholder)

### Reports
- `GET /api/reports/keyword-frequency?top_n=20` - Top keywords
- `GET /api/reports/source-summary` - Documents per source
- `GET /api/reports/crawl-timeline?days=30` - Activity timeline
- `GET /api/reports/export/csv?report_type=keywords` - CSV export
- `GET /api/reports/export/pdf?report_type=keywords` - PDF export

### Health
- `GET /health` - System health check

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Suites
```bash
# Parser tests
pytest tests/test_parsers.py -v
pytest tests/test_social_parsers.py -v

# NLP tests
pytest tests/test_keywords.py -v

# Blocking detection tests
pytest tests/test_blocking.py -v

# Configuration tests
pytest tests/test_config_enforcement.py -v

# API tests
pytest tests/test_api.py -v
```

### Expected Results
All tests should pass. Some tests may be skipped if optional dependencies (NLTK data, sklearn, RAKE) are not available.

## 🛠️ Configuration

### Cron Expressions
Format: `minute hour day month weekday`

Examples:
- `0 0 * * *` - Daily at midnight
- `0 */6 * * *` - Every 6 hours
- `30 8 * * 1-5` - Weekdays at 8:30 AM
- `0 0 1 * *` - First day of each month
- `0 0 * * 0` - Every Sunday

Validator: https://crontab.guru/

### Rate Limiting
- **Minimum**: 1 request/minute (60s delay)
- **Maximum**: 300 requests/minute (0.2s delay)
- **Recommended**: 30-60 requests/minute for web sources
- **Social Media**: Respect platform limits (Reddit: 60/min, Twitter via Nitter: 30/min)

### Max Hits
- **Minimum**: 1 page
- **Maximum**: 10,000 pages
- **Recommended**: 50-100 for blogs, 500+ for news aggregators
- **Strict Enforcement**: Crawl stops exactly at max_hits

## ⚠️ Common Errors & Fixes

### MongoDB Connection Failed
**Error**: `ServerSelectionTimeoutError`
**Fix**: 
1. Ensure MongoDB is running: `net start MongoDB`
2. Check MONGODB_URI in `.env`
3. For Atlas, verify connection string and IP whitelist

### NLTK Data Not Found
**Error**: `Resource punkt not found`
**Fix**:
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
```

### Source Status BLOCKED
**Cause**: HTTP 403/429, CAPTCHA, or IP ban detected
**Fix**:
1. Check "Monitoring" tab for block reason
2. Reduce rate_limit_per_minute (try 10-20)
3. Increase CRAWLER_DELAY in `.env`
4. Wait before retrying (some blocks are temporary)
5. For persistent blocks, source may require authentication

### Port 8000 Already in Use
**Error**: `Address already in use`
**Fix**:
1. Find process: `netstat -ano | findstr :8000`
2. Kill process: `taskkill /PID <pid> /F`
3. Or change API_PORT in `.env`

### Keyword Extraction Returns Empty List
**Cause**: Text too short or all stopwords
**Fix**:
1. Ensure documents have meaningful content
2. Check if text_cleaner is removing too much
3. Lower min_freq in keyword extractor

## 📊 Lab Requirements Mapping

### Lab 2: Web Crawler ✅
- ✅ Configurable source management
- ✅ HTML, RSS, PDF, TXT parsing
- ✅ MongoDB storage with text indexing
- ✅ Pagination support
- ✅ Cron-based scheduling
- ✅ Max hits enforcement
- ✅ Keyword search with boolean operators
- ✅ Full crawl workflow implemented

### Lab 3: Reporting & Dashboard ✅
- ✅ Web dashboard with 5 tabs
- ✅ Crawl activity visualization (charts)
- ✅ Data statistics display
- ✅ Search functionality with highlighting
- ✅ Keyword frequency reports (intelligent NLP)
- ✅ Source-based summaries
- ✅ CSV and PDF export capabilities
- ✅ Real-time monitoring

### Enhancements (Beyond Requirements)
- ✅ Social media source support (Twitter, Reddit, YouTube, LinkedIn)
- ✅ Intelligent NLP keyword extraction (TF-IDF, RAKE, lemmatization)
- ✅ Blocking detection system (HTTP codes, CAPTCHA, IP bans)
- ✅ Advanced rate limiting (requests/minute)
- ✅ Retry policies with exponential backoff
- ✅ Platform comparison analytics
- ✅ Comprehensive test suite (8 test files)

## 🏗️ Architecture

```
Web Analytics Project/
├── src/
│   ├── api/                    # FastAPI routes (5 routers)
│   │   ├── main.py            # App initialization
│   │   ├── sources.py         # Source CRUD
│   │   ├── crawler.py         # Crawl control
│   │   ├── search.py          # Search endpoint
│   │   └── reports.py         # Reports & exports
│   ├── crawler/               # Crawling logic
│   │   ├── base_crawler.py    # HTTP client with politeness
│   │   ├── crawl_manager.py   # Orchestration + blocking detection
│   │   ├── scheduler.py       # APScheduler integration
│   │   ├── blocking_detector.py # Block detection system
│   │   └── parsers/           # Content parsers
│   │       ├── html_parser.py
│   │       ├── rss_parser.py
│   │       ├── pdf_parser.py
│   │       ├── txt_parser.py
│   │       ├── twitter_parser.py
│   │       ├── reddit_parser.py
│   │       ├── youtube_parser.py
│   │       └── linkedin_parser.py
│   ├── processing/            # NLP & Search
│   │   ├── text_cleaner.py    # Text normalization
│   │   ├── intelligent_keywords.py  # NLP extraction
│   │   └── search.py          # Search engine
│   ├── storage/               # Data layer
│   │   ├── models.py          # Pydantic models
│   │   └── mongo.py           # MongoDB operations
│   ├── dashboard/             # Frontend
│   │   ├── templates/
│   │   │   └── index.html     # Main UI
│   │   └── static/
│   │       ├── css/style.css  # Dark theme + glassmorphism
│   │       └── js/
│   │           ├── app.js     # Core logic + social media
│   │           ├── charts.js  # Chart.js visualizations
│   │           └── search.js  # Search UI
│   └── utils/                 # Shared utilities
│       ├── config.py          # Environment config
│       └── logger.py          # Logging setup
├── tests/                     # Test suite
│   ├── test_parsers.py
│   ├── test_social_parsers.py
│   ├── test_keywords.py
│   ├── test_blocking.py
│   ├── test_config_enforcement.py
│   ├── test_crawler.py
│   └── test_api.py
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── .env                       # Configuration (not in git)
├── .env.example              # Configuration template
├── .gitignore                # Git exclusions
└── README.md                 # This file
```

## 📝 License

Academic project for Web Analytics course. Not for commercial use without permission.

## 🙏 Acknowledgments

- **BeautifulSoup4**: HTML parsing
- **NLTK**: Natural language processing
- **scikit-learn**: Machine learning utilities
- **FastAPI**: Modern API framework
- **Chart.js**: Data visualization
- **MongoDB**: Document database
- **APScheduler**: Job scheduling

---

**Project Status**: ✅ Production-ready | Fully tested | Portfolio-ready

**Version**: 2.0.0 (Enhanced with Social Media & Intelligent NLP)

**Last Updated**: December 2025
