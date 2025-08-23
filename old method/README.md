# 📚 Bihar ul Anwar RAG System

A powerful AI-powered search and retrieval system for **Bihar ul Anwar** - the comprehensive 110-volume collection of Shia Islamic traditions compiled by Allama Muhammad Baqir Majlisi.

## 🌟 What is This Project?

This project creates an intelligent search system that allows you to:
- **Search across processed volumes** of Bihar ul Anwar instantly
- **Ask questions in natural language** and get accurate answers with proper references
- **Find specific hadiths** by volume, chapter, or hadith number
- **Get responses in both Arabic and English** with proper Islamic honorifics
- **Receive precise citations** (e.g., "Bihar ul Anwar, Volume 15, Chapter 3, Hadith 7")

### 📖 About Bihar ul Anwar

Bihar ul Anwar (بحار الأنوار - "Oceans of Light") is one of the most comprehensive collections of Shia hadith, containing:
- **110 volumes** of Islamic traditions
- Hadiths about Prophet Muhammad (PBUH), Ahlul Bayt (AS), and the Twelve Imams
- Topics covering theology, history, ethics, and eschatology
- Both **Arabic original text** and **English translations**

## 🚀 Key Features

- **🔍 Intelligent Search**: Uses Google's Gemini 2.5 Flash Lite AI for fast context understanding
- **🔢 Bilingual Support**: Processes both Arabic and English text with smart separation
- **🎯 Precise References**: Returns exact volume, chapter, and hadith numbers when available
- **⚡ Fast Retrieval**: Vector similarity search using PostgreSQL + pgvector
- **🌐 API Interface**: RESTful API with comprehensive Swagger documentation
- **📊 Production Ready**: Optimized for performance with concurrent processing
- **🔧 Modular Architecture**: Clean separation of concerns across multiple files

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python) with async support
- **AI Model**: Google Gemini 2.5 Flash Lite (via Gemini API)
- **Database**: PostgreSQL with pgvector extension for vector similarity
- **Vector Embeddings**: Google's text-embedding-004 model (768 dimensions)
- **PDF Processing**: PyPDF with memory optimization
- **Text Splitting**: LangChain RecursiveCharacterTextSplitter
- **Concurrent Processing**: ThreadPoolExecutor for batch operations

## 📁 Project Structure (Current)
rag-for-ba/
├── main.py                      # FastAPI application and routes (10.4KB)
├── config.py                    # Configuration and settings (2.2KB)
├── database.py                  # Database operations and models (10.4KB)
├── processing.py                # PDF processing and embeddings (9.0KB)
├── process_bihar_volumes.py     # Optimized batch processor (9.1KB)
├── test_single_volume.py        # Single volume testing (7.5KB)
├── test_volume_7_queries.py     # Volume 7 content-specific testing (11.1KB)
├── test_queries.py              # General query testing (5.9KB)
├── fixes.py                     # Diagnostic and debugging tools (4.1KB)
├── debug_issues.py              # Additional debugging utilities (4.9KB)
├── requirements.txt             # Python dependencies (153B)
├── .env                         # Environment configuration (142B)
├── .gitignore                   # Git ignore patterns (60B)
├── README.md                    # Project documentation (8.9KB)
├── output7.md                   # Volume 7 test output/results (8.5KB)
├── Bihar_Al_Anwaar_PDFs/        # PDF collection directory
│   ├── BiharAlAnwaar_V1.pdf     # Volume 1 (2.2MB)
│   ├── BiharAlAnwaar_V2.pdf     # Volume 2 (4.2MB)
│   ├── BiharAlAnwaar_V3.pdf     # Volume 3 (3.7MB)
│   ├── ...                      # Volumes 4-93
│   └── BiharAlAnwaar_V94.pdf    # Volume 94 (6.7MB)
├── data-collection/             # Data collection scripts/tools
├── __pycache__/                 # Python cache files (auto-generated)
└── venv/                        # Virtual environment

## 📋 File Descriptions:
**Core Application Files:**

main.py - Main FastAPI application with API routes and endpoints
config.py - Centralized configuration management and settings
database.py - Database operations, models, and vector search functions
processing.py - PDF text extraction, embedding generation, and text processing

**Processing & Batch Operations:**

process_bihar_volumes.py - Production batch processor for all volumes
test_single_volume.py - Single volume testing and validation
test_volume_7_queries.py - Content-specific testing for Volume 7
test_queries.py - General system testing with sample queries

**Debugging & Utilities:**

fixes.py - Diagnostic tools and system health checks
debug_issues.py - Advanced debugging and troubleshooting utilities
output7.md - Volume 7 test results and analysis

**Configuration & Dependencies:**

requirements.txt - Python package dependencies
.env - Environment variables (API keys, database config)
.gitignore - Git ignore patterns
README.md - Project documentation and setup guide

**Data Directories:**

Bihar_Al_Anwaar_PDFs/ - Contains 94 Bihar ul Anwar PDF volumes (~444MB total)
data-collection/ - Additional data collection scripts and tools
venv/ - Python virtual environment (auto-generated)
__pycache__/ - Python bytecode cache (auto-generated)

## 📊 Project Statistics:

Total Files: 16 core files + 94 PDFs
Code Size: ~75KB of Python code
PDF Collection: ~444MB (94 volumes)
Architecture: Modular, production-ready structure

## 📊 Current System Status

### ✅ What's Working:
- **7 volumes processed** with full embeddings (6,481 total chunks)
- **71% query success rate** on complex queries
- **Perfect volume filtering** and content retrieval
- **Stable concurrent processing** with retry mechanisms
- **Production-ready API** with comprehensive error handling

### 🎯 Performance Metrics:
- **Response Time**: 6-9 seconds for complex queries
- **Embedding Generation**: 768-dimensional vectors for all chunks
- **Database**: All chunks have valid embeddings
- **Search Accuracy**: High relevance for specific topics

### 📈 Test Results (Volume 7):
- ✅ Resurrection proof queries: Excellent results
- ✅ Scale (Mizan) content: Perfect chapter detection
- ✅ Judgment Day scenarios: Good contextual responses
- ⚠️ Some edge case queries need more data

## 🔧 Installation & Setup

### Prerequisites

- Python 3.8+
- PostgreSQL 12+ with pgvector extension
- Google AI API key (Gemini)
- Bihar ul Anwar PDF files (available from hubeali.com)

### Quick Start

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd rag-for-ba
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings:
# GOOGLE_API_KEY=your-key-here
# DB_HOST=localhost
# DB_NAME=bihar
# DB_USER=postgres
# DB_PASSWORD=your-password

# 4. Setup database
createdb bihar
psql bihar -c "CREATE EXTENSION vector;"

# 5. Start the system
uvicorn main:app --reload
```

### Download PDFs (Optional)

Use the included Jupyter notebook to download all 94 volumes:

```bash
jupyter notebook selenium_for_pdf.ipynb
```

## 🚀 Usage Guide

### 1. **Processing Volumes**

```bash
# Test single volume first
python test_single_volume.py

# Process all volumes (production)
python process_bihar_volumes.py

# Monitor progress and get reports
```

### 2. **API Usage**

Visit `http://localhost:8000/docs` for interactive API documentation.

**Example Query:**
```python
import requests+

response = requests.post("http://localhost:8000/query", json={
    "query": "What does Bihar ul Anwar say about the Scale of Justice?",
    "top_k": 5,
    "include_arabic": True,
    "volume_filter": 7  # Optional: search specific volume
})

result = response.json()
print(f"Found {result['total_sources']} sources")
print(f"Answer: {result['answer']}")
```

### 3. **Testing System**

```bash
# Test specific volume content
python test_volume_7_queries.py

# Run diagnostics
python fixes.py

# General query testing
python test_queries.py
```

## 📋 API Endpoints

| Endpoint | Method | Description | Status |
|----------|--------|-------------|---------|
| `/` | GET | System health and statistics | ✅ Working |
| `/query` | POST | Natural language search | ✅ Working |
| `/process-volume` | POST | Process single PDF | ✅ Working |
| `/volumes` | GET | List processed volumes | ✅ Working |
| `/statistics` | GET | Database statistics | ✅ Working |
| `/search-by-reference` | GET | Search by volume/chapter/hadith | ⚠️ Needs fixing |

## 🎯 Production Optimizations

### **Memory Management:**
- Page-limited processing (200 pages max per volume)
- Batch insertion (50 chunks at a time)
- Connection pooling for database operations

### **Performance Tuning:**
- Concurrent volume processing (2 simultaneous)
- Optimized chunk size (800 characters)
- Rate-limited API calls (200ms delays)
- Vector index optimization

### **Error Handling:**
- Automatic retry mechanisms
- Graceful fallbacks for failed embeddings
- Comprehensive logging and monitoring

## 🔍 Troubleshooting

### **Common Issues & Solutions:**

1. **Slow Query Response (>10 seconds)**
   ```bash
   # Check database connections and restart
   sudo systemctl restart postgresql
   uvicorn main:app --reload
   ```

2. **Embedding Generation Errors**
   ```bash
   # Test API connectivity
   python fixes.py
   # Check API quota in Google AI Studio
   ```

3. **Reference Search 500 Errors**
   ```bash
   # Check database.py search_by_reference function
   # Ensure proper error handling in SQL queries
   ```

4. **Memory Issues During Processing**
   ```bash
   # Reduce concurrent volumes in process_bihar_volumes.py
   CONCURRENT_VOLUMES = 1
   ```

## 📊 System Monitoring

### **Check System Health:**
```bash
# API status
curl http://localhost:8000/

# Database statistics
curl http://localhost:8000/statistics

# Test specific functionality
python test_single_volume.py
```

### **Performance Metrics:**
- Monitor response times in server logs
- Check database connection pools
- Track embedding generation success rates
- Monitor API rate limit usage

## 🎯 Current Limitations

1. **Volume Coverage**: 7/110 volumes processed (more needed for comprehensive coverage)
2. **Query Success Rate**: 71% (some complex queries need improvement)
3. **Reference Search**: Currently experiencing 500 errors
4. **Response Time**: 6-9 seconds (target: 2-3 seconds)

## 🚀 Next Steps

### **Immediate Actions:**
1. ✅ Fix reference search functionality
2. 🔄 Process additional 10-20 volumes for testing
3. 📈 Optimize query response times
4. 🔧 Improve metadata extraction

### **Future Enhancements:**
- [ ] Complete all 110 volumes
- [ ] Implement hadith authentication
- [ ] Add cross-referencing with other collections
- [ ] Create web interface
- [ ] Add export functionality
- [ ] Multi-language support (Urdu, Persian)

## 🤝 Contributing

This project welcomes contributions! Areas needing help:

1. **Volume Processing**: Help process remaining 103 volumes
2. **Performance Optimization**: Improve query response times
3. **Metadata Enhancement**: Better chapter/hadith extraction
4. **Testing**: Add more comprehensive test coverage
5. **Documentation**: Improve API documentation

## 📜 License & Ethics

This project is for **educational and research purposes**. Bihar ul Anwar texts are in the public domain. The system is designed to preserve and make accessible Islamic scholarly works for academic study.

## 🙏 Acknowledgments

- **Allama Muhammad Baqir Majlisi** - Original compiler of Bihar ul Anwar
- **Hubeali.com** - Digital source of PDF volumes
- **Google AI** - Gemini API for embeddings and chat
- **PostgreSQL & pgvector** - Vector similarity search
- **FastAPI Community** - Web framework and ecosystem

---

## 🔗 Quick Links

- **API Documentation**: http://localhost:8000/docs
- **System Statistics**: http://localhost:8000/statistics
- **Health Check**: http://localhost:8000/
- **ReDoc**: http://localhost:8000/redoc

---

**⭐ Star this repository if you find it useful for Islamic research!**

*Last Updated: Current system status as of testing phase*