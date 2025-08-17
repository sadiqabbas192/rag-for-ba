# 📚 Bihar ul Anwar RAG System

A powerful AI-powered search and retrieval system for **Bihar ul Anwar** - the comprehensive 110-volume collection of Shia Islamic traditions compiled by Allama Muhammad Baqir Majlisi.

## 🌟 What is This Project?

This project creates an intelligent search system that allows you to:
- **Search across all 110 volumes** of Bihar ul Anwar instantly
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

- **🔍 Intelligent Search**: Uses Google's Gemini 2.0 Flash AI to understand context and meaning
- **📑 Bilingual Support**: Processes both Arabic and English text
- **🎯 Precise References**: Returns exact volume, chapter, and hadith numbers
- **⚡ Fast Retrieval**: Vector similarity search using PostgreSQL + pgvector
- **🌐 API Interface**: RESTful API with Swagger documentation
- **🔄 n8n Integration**: Ready for workflow automation
- **📊 94 Volumes Included**: Currently has volumes 1-94 processed

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python)
- **AI Model**: Google Gemini 2.0 Flash (via Gemini API)
- **Database**: PostgreSQL with pgvector extension
- **Vector Embeddings**: Google's text-embedding-004 model
- **PDF Processing**: PyPDF2
- **Text Splitting**: LangChain
- **Workflow Automation**: n8n (optional)

## 📁 Project Structure

```
rag-for-ba/
├── main.py                      # Main FastAPI application
├── process_bihar_volumes.py     # Batch processor for PDFs
├── test_queries.py             # Test script with sample queries
├── requirements.txt            # Python dependencies
├── .env                       # Configuration (API keys, database)
├── .gitignore                # Git ignore file
├── selenium_for_pdf.ipynb    # Notebook for downloading PDFs
├── Bihar_Al_Anwaar_PDFs/     # Folder containing 94 PDF volumes
   |──BiharAlAnwaar_V1.pdf
   |──BiharAlAnwaar_V2.pdf
   |──BiharAlAnwaar_V3.pdf
   |──BiharAlAnwaar_V4.pdf
   |──BiharAlAnwaar_V5.pdf
   |──BiharAlAnwaar_Vx.pdf
   |──BiharAlAnwaar_V94.pdf
   |──
└── venv/                     # Virtual environment folder
```

## 🔧 Installation & Setup

### Prerequisites

- Python 3.8+
- PostgreSQL with pgvector extension
- Google AI API key (Gemini)
- 94 Bihar ul Anwar PDF files

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/rag-for-ba.git
cd rag-for-ba
```

### Step 2: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 3: Set Up PostgreSQL with pgvector

```sql
-- Install pgvector extension (download from https://github.com/pgvector/pgvector)
CREATE EXTENSION vector;

-- The tables will be created automatically when you run the app
```

### Step 4: Configure Environment Variables

Create a `.env` file with your configuration:

```env
GOOGLE_API_KEY=your-google-ai-api-key-here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bihar
DB_USER=postgres
DB_PASSWORD=your-password
```

### Step 5: Start the FastAPI Server

```bash
python main.py
```

The server will start at `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Step 6: Process Bihar ul Anwar Volumes

```bash
# Update the PDF folder path in process_bihar_volumes.py
# Then run:
python process_bihar_volumes.py
```

This will process all 94 PDF volumes and create vector embeddings for search.

### Step 7: Test the System

```bash
python test_queries.py
```

## 📝 How to Use

### 1. Using the API (Swagger UI)

Visit `http://localhost:8000/docs` for an interactive API interface where you can:
- Test queries
- Search by references
- View statistics
- Process new volumes

### 2. Example Queries

```python
# Ask about creation traditions
"What are the traditions about the creation of Prophet Muhammad (PBUH)?"

# Find specific topics
"What does Bihar ul Anwar say about Ghadir Khumm?"

# Search for Imam-related content
"Find hadiths about the twelve Imams and their names"

# Query about signs of Imam Mahdi
"What are the signs of appearance of Imam Mahdi?"
```

### 3. API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/query` | POST | Search Bihar ul Anwar with natural language |
| `/process-volume` | POST | Process a single volume PDF |
| `/batch-process` | POST | Process multiple volumes |
| `/search-by-reference` | GET | Find specific hadith by volume/chapter/number |
| `/volumes` | GET | List all processed volumes |
| `/statistics` | GET | Get system statistics |
| `/documents` | GET | List all documents in database |

### 4. Sample API Request

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the virtues of Imam Ali?",
    "top_k": 5,
    "include_arabic": true
  }'
```

## 🔄 n8n Integration

The system is designed to work with n8n workflows. Simply use HTTP Request nodes to call the API endpoints. No AI Agent node needed - the FastAPI backend handles everything.

### n8n Workflow Example:

1. **Webhook Trigger** → Receive user question
2. **HTTP Request** → Call `/query` endpoint
3. **Response** → Return formatted answer with references

## 📊 Current Status

- **Volumes Processed**: 94 out of 110
- **Total Chunks**: ~10,000+ searchable text segments
- **Languages**: Arabic & English
- **Database Size**: ~450 MB

### Missing Volumes (95-110)

The following volumes are not yet included:
- Volumes 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Add Missing Volumes**: Help process volumes 95-110
2. **Improve Text Extraction**: Better Arabic/English separation
3. **Enhance Reference Detection**: Improve chapter/hadith number extraction
4. **Add Features**: Additional search filters, export options, etc.

## ⚠️ Important Notes

1. **PDF Quality**: The quality of search results depends on PDF text quality
2. **Translation Accuracy**: English translations may have variations
3. **Processing Time**: Initial processing of all volumes takes 30-60 minutes
4. **API Rate Limits**: Gemini API has rate limits (adjust batch size if needed)
5. **Database Size**: Ensure sufficient disk space for PostgreSQL

## 🐛 Troubleshooting

### Common Issues:

1. **"Database connection failed"**
   - Ensure PostgreSQL is running
   - Check credentials in `.env` file
   - Verify pgvector extension is installed

2. **"No text extracted from PDF"**
   - Check if PDFs are text-based (not scanned images)
   - Try different PDF extraction methods

3. **"Embedding error"**
   - Verify Google API key is valid
   - Check API quota/limits

4. **"No results found"**
   - Ensure volumes are processed (`/statistics` endpoint)
   - Try broader search terms

## 📜 License

This project is for educational and research purposes. Bihar ul Anwar texts are in the public domain.

## 🙏 Acknowledgments

- **Allama Muhammad Baqir Majlisi** - Compiler of Bihar ul Anwar
- **Hubeali.com** - Source of digital Bihar ul Anwar PDFs
- **Google AI** - For Gemini API
- **PostgreSQL** - For pgvector extension

## 📞 Support

For issues or questions:
1. Check the [Issues](https://github.com/yourusername/rag-for-ba/issues) section
2. Review API documentation at `/docs`
3. Run test queries with `test_queries.py`

## 🎯 Future Enhancements

- [ ] Add remaining volumes (95-110)
- [ ] Implement hadith authentication (sahih/weak classification)
- [ ] Add narrator chain (isnad) analysis
- [ ] Create mobile app interface
- [ ] Add export functionality (PDF/DOCX reports)
- [ ] Implement multi-language support (Urdu, Persian, etc.)
- [ ] Add cross-reference with other hadith collections

---

**Note**: This system is designed to preserve and make accessible the valuable knowledge contained in Bihar ul Anwar for research and educational purposes.

🌟 **Star this repository if you find it useful!**