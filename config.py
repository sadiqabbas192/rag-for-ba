# config.py - Configuration and Settings
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_TIMEOUT = 120  # 2 minutes
GEMINI_TIMEOUT = 90  # 1.5 minutes

# ===================== Configuration =====================
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'bihar'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD')
}

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)
EMBEDDING_MODEL = 'models/text-embedding-004'
CHAT_MODEL = genai.GenerativeModel('gemini-2.5-flash-lite')

# System Prompt for Bihar ul Anwar
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

# Processing Configuration
MAX_PAGES_PER_VOLUME = 200
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
EMBEDDING_BATCH_SIZE = 3
DB_BATCH_SIZE = 50