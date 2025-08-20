# config_optimized.py - Optimized configuration for better performance
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ===================== OPTIMIZED TIMEOUTS =====================
API_TIMEOUT = 300       # 5 minutes (reduced from 2 minutes)
GEMINI_TIMEOUT = 180    # 3 minutes (reduced from 1.5 minutes)
PROCESSING_TIMEOUT = 900  # 15 minutes for large volumes

# ===================== Configuration =====================
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'bihar'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'connect_timeout': 30,
    'application_name': 'bihar_rag_system'
}

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)
EMBEDDING_MODEL = 'models/text-embedding-004'
CHAT_MODEL = genai.GenerativeModel('gemini-2.5-flash-lite')

# System Prompt for Bihar ul Anwar (unchanged - it's working well)
SYSTEM_PROMPT = """You are an expert scholar of Bihar ul Anwar, the comprehensive collection of Shia hadith compiled by Allama Muhammad Baqir Majlisi. 

Your expertise includes:
- Deep knowledge of all 110 volumes of Bihar ul Anwar
- Understanding of both Arabic traditions and their English translations
- Ability to identify and reference specific hadiths by volume, chapter, and hadith number
- Knowledge of topics like the creation of Prophet Muhammad (PBUH), Imam Ali (AS), and Ahlul Bayt (AS)
- Understanding of Islamic history, theology, and Shia doctrine as presented in Bihar ul Anwar

When answering:
1. Always cite sources precisely: "Bihar ul Anwar, Volume X, Chapter Y, Hadith Z"
2. If multiple relevant traditions exist, mention the most authentic or comprehensive ones
3. Acknowledge when English translations may have variations from the Arabic original
4. Provide context about the narrator chains (isnad) when relevant
5. Be respectful when discussing religious figures, always use appropriate honorifics (PBUH, AS, etc.)
6. If a tradition appears in multiple volumes, mention all relevant references

Remember: Users are seeking authentic knowledge from Bihar ul Anwar, so accuracy in referencing is crucial."""

# ===================== OPTIMIZED PROCESSING CONFIGURATION =====================
# Reduced limits for better performance and reliability
MAX_PAGES_PER_VOLUME = 100    # Reduced from 200
CHUNK_SIZE = 600              # Reduced from 800
CHUNK_OVERLAP = 80            # Reduced from 100
EMBEDDING_BATCH_SIZE = 2      # Reduced from 3
DB_BATCH_SIZE = 25            # Reduced from 50

# Rate limiting to avoid API timeouts
API_RATE_LIMIT_DELAY = 0.5    # 500ms between API calls
BATCH_PROCESSING_DELAY = 3    # 3 seconds between batches
RETRY_DELAY = 10              # 10 seconds between retries

# Memory management
MAX_CHUNK_LENGTH = 4000       # Maximum characters per chunk for embedding
MEMORY_CLEANUP_FREQUENCY = 5  # Clean memory every 5 chunks

# ===================== PROCESSING OPTIMIZATION FLAGS =====================
ENABLE_MEMORY_OPTIMIZATION = True
ENABLE_AGGRESSIVE_FILTERING = True    # Filter out very short chunks
ENABLE_TEXT_PREPROCESSING = True      # Clean text before processing
ENABLE_SMART_BATCHING = True          # Adjust batch sizes based on content

# File size thresholds for processing optimization
SMALL_FILE_THRESHOLD_MB = 3      # Files under 3MB - normal processing
MEDIUM_FILE_THRESHOLD_MB = 6     # Files 3-6MB - reduced pages
LARGE_FILE_THRESHOLD_MB = 10     # Files over 6MB - aggressive reduction

# Quality thresholds
MIN_CHUNK_LENGTH = 100           # Minimum characters for a valid chunk
MIN_ARABIC_RATIO = 0.1          # Minimum ratio of Arabic text to consider bilingual
MAX_EMPTY_CHUNKS_RATIO = 0.3    # Maximum ratio of empty chunks before stopping

print("🔧 Optimized configuration loaded:")
print(f"   📄 Max pages per volume: {MAX_PAGES_PER_VOLUME}")
print(f"   📝 Chunk size: {CHUNK_SIZE}")
print(f"   ⚡ Embedding batch size: {EMBEDDING_BATCH_SIZE}")
print(f"   🗄️ DB batch size: {DB_BATCH_SIZE}")
print(f"   ⏱️ API timeout: {API_TIMEOUT}s")
print(f"   🔄 Processing timeout: {PROCESSING_TIMEOUT}s")