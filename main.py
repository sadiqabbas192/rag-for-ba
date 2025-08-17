# main.py - Bihar ul Anwar RAG System with Simplified Functions
import os
import re
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
import json

# FastAPI with Swagger
from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

# PDF processing
from pypdf import PdfReader

# Text splitting
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Google Gemini
import google.generativeai as genai

# Database
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from pgvector.psycopg2 import register_vector

# Environment
from dotenv import load_dotenv
load_dotenv()

# ===================== Configuration =====================
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'bihar_anwar_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD')
}

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)
EMBEDDING_MODEL = 'models/text-embedding-004'
CHAT_MODEL = genai.GenerativeModel('gemini-2.0-flash-exp')

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

# Database connection pool
db_conn = None

# ===================== Pydantic Models =====================
class QueryRequest(BaseModel):
    """Request model for querying Bihar ul Anwar"""
    query: str = Field(..., 
        description="Question about Bihar ul Anwar content",
        example="What are the traditions about the creation of Prophet Muhammad?")
    top_k: int = Field(7, 
        description="Number of relevant passages to retrieve",
        ge=1, le=20)
    include_arabic: bool = Field(True, 
        description="Include Arabic text in response")
    volume_filter: Optional[int] = Field(None, 
        description="Filter by specific volume number (1-110)",
        ge=1, le=110)

class HadithResponse(BaseModel):
    """Response model for hadith queries"""
    success: bool
    query: str
    answer: str
    references: List[Dict[str, Any]]
    processing_time: float
    total_sources: int

class ProcessingRequest(BaseModel):
    """Request for processing Bihar ul Anwar volumes"""
    file_path: str = Field(..., 
        description="Path to Bihar ul Anwar PDF",
        example="C:/BiharUlAnwar/Volume_1.pdf")
    volume_number: int = Field(..., 
        description="Volume number (1-110)",
        ge=1, le=110)
    language: str = Field("mixed", 
        description="Content language: arabic, english, or mixed")

# ===================== FastAPI App Setup =====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    print("🚀 Starting Bihar ul Anwar RAG System...")
    print("📚 System designed for 110 volumes of Bihar ul Anwar")
    print("🔍 Swagger UI will be available at: http://localhost:8000/docs")
    
    # Initialize database (this was in your old startup event)
    try:
        init_database()
        print("✅ Bihar ul Anwar RAG System started")
        print("📖 Access Swagger UI at: http://localhost:8000/docs")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        # Don't raise the exception, let the app start anyway
    
    yield
    
    # Shutdown code
    global db_conn
    if db_conn:
        db_conn.close()
        print("Database connection closed")
    print("📚 Shutting down...")

app = FastAPI(
    title="Bihar ul Anwar RAG System",
    description="""
    ## Comprehensive Search System for Bihar ul Anwar (110 Volumes)
    
    This API provides intelligent search and retrieval from all 110 volumes of Bihar ul Anwar,
    supporting both Arabic and English text with precise hadith referencing.
    
    ### Features:
    - Search across all 110 volumes
    - Bilingual support (Arabic + English)
    - Precise hadith referencing (Volume, Chapter, Hadith number)
    - Context-aware responses using Gemini 2.0 Flash
    - Vector similarity search for finding related traditions
    """,
    version="1.0.0",
    docs_url="/docs",   # Swagger UI
    redoc_url="/redoc",  # ReDoc UI
    lifespan=lifespan
)

# CORS for n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== Database Functions =====================
def get_db_connection():
    """Get or create database connection"""
    global db_conn
    if db_conn is None or db_conn.closed:
        db_conn = psycopg2.connect(**DB_CONFIG)
        register_vector(db_conn)
    return db_conn

def init_database():
    """Initialize database tables for Bihar ul Anwar"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create pgvector extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        
        # Main table for hadith chunks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bihar_chunks (
                id SERIAL PRIMARY KEY,
                volume_number INTEGER NOT NULL,
                chapter_name VARCHAR(500),
                hadith_number VARCHAR(100),
                arabic_text TEXT,
                english_text TEXT,
                full_text TEXT NOT NULL,
                chunk_index INTEGER,
                embedding vector(768),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Indexes for faster search
                INDEX idx_volume (volume_number),
                INDEX idx_hadith (hadith_number)
            )
        """)
        
        # Index for vector search
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bihar_embedding 
            ON bihar_chunks 
            USING ivfflat (embedding vector_cosine_ops) 
            WITH (lists = 100)
        """)
        
        # Table for tracking processed volumes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_volumes (
                id SERIAL PRIMARY KEY,
                volume_number INTEGER UNIQUE,
                file_name VARCHAR(255),
                total_chunks INTEGER,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("✅ Database initialized for Bihar ul Anwar")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Database initialization error: {e}")
        raise
    finally:
        cursor.close()

# ===================== Text Processing Functions =====================
def extract_hadith_metadata(text: str, volume_num: int) -> Dict:
    """Extract hadith metadata from text"""
    metadata = {
        'volume': volume_num,
        'chapter': None,
        'hadith_number': None
    }
    
    # Pattern matching for hadith references
    # Looking for patterns like "Chapter 5", "Hadith 10", "Tradition #10", etc.
    chapter_match = re.search(r'Chapter\s+(\d+)|Bab\s+(\d+)', text, re.IGNORECASE)
    hadith_match = re.search(r'Hadith\s+#?(\d+)|Tradition\s+#?(\d+)|Riwayat\s+(\d+)', text, re.IGNORECASE)
    
    if chapter_match:
        metadata['chapter'] = chapter_match.group(1) or chapter_match.group(2)
    
    if hadith_match:
        metadata['hadith_number'] = hadith_match.group(1) or hadith_match.group(2) or hadith_match.group(3)
    
    return metadata

def split_arabic_english(text: str) -> tuple:
    """Separate Arabic and English text"""
    arabic_text = ""
    english_text = ""
    
    lines = text.split('\n')
    for line in lines:
        # Check if line contains Arabic characters
        if any('\u0600' <= char <= '\u06FF' for char in line):
            arabic_text += line + "\n"
        else:
            english_text += line + "\n"
    
    return arabic_text.strip(), english_text.strip()

def process_pdf_text(pdf_path: str, volume_num: int) -> List[Dict]:
    """Extract and process text from Bihar ul Anwar PDF"""
    try:
        reader = PdfReader(pdf_path)
        
        # Text splitter optimized for hadith content
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # Larger chunks to keep hadiths together
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "।", "۔"],  # Include Arabic/Urdu punctuation
            length_function=len
        )
        
        all_chunks = []
        
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            if not text:
                continue
            
            # Split into chunks
            chunks = splitter.split_text(text)
            
            for chunk_idx, chunk in enumerate(chunks):
                # Separate Arabic and English
                arabic, english = split_arabic_english(chunk)
                
                # Extract metadata
                metadata = extract_hadith_metadata(chunk, volume_num)
                metadata['page'] = page_num
                
                chunk_data = {
                    'volume_number': volume_num,
                    'arabic_text': arabic,
                    'english_text': english,
                    'full_text': chunk,
                    'chunk_index': chunk_idx,
                    'metadata': metadata
                }
                
                all_chunks.append(chunk_data)
        
        return all_chunks
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")

# ===================== Embedding Functions =====================
def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using Gemini"""
    embeddings = []
    batch_size = 10
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        for text in batch:
            try:
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=text,
                    task_type="RETRIEVAL_DOCUMENT"
                )
                embeddings.append(result['embedding'])
            except Exception as e:
                print(f"Embedding error: {e}")
                embeddings.append([0.0] * 768)
    
    return embeddings

def search_similar_chunks(query: str, top_k: int = 7, volume_filter: Optional[int] = None) -> List[Dict]:
    """Search for similar chunks using vector similarity"""
    # Generate query embedding
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=query,
        task_type="RETRIEVAL_QUERY"
    )
    query_embedding = result['embedding']
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Build query with optional volume filter
    base_query = """
        SELECT 
            volume_number,
            chapter_name,
            hadith_number,
            arabic_text,
            english_text,
            full_text,
            metadata,
            1 - (embedding <=> %s::vector) as similarity
        FROM bihar_chunks
        WHERE 1 - (embedding <=> %s::vector) > 0.3
    """
    
    if volume_filter:
        base_query += f" AND volume_number = {volume_filter}"
    
    base_query += """
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """
    
    cursor.execute(base_query, (query_embedding, query_embedding, query_embedding, top_k))
    results = cursor.fetchall()
    cursor.close()
    
    return results

# ===================== Response Generation =====================
def generate_answer_with_context(query: str, chunks: List[Dict], include_arabic: bool = True) -> str:
    """Generate answer using Gemini with Bihar ul Anwar context"""
    
    # Prepare context from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        volume = chunk.get('volume_number', 'Unknown')
        metadata = chunk.get('metadata', {})
        chapter = metadata.get('chapter', 'Unknown')
        hadith_num = metadata.get('hadith_number', 'Unknown')
        
        context_part = f"\n[Source {i}] Bihar ul Anwar, Volume {volume}"
        if chapter != 'Unknown':
            context_part += f", Chapter {chapter}"
        if hadith_num != 'Unknown':
            context_part += f", Hadith {hadith_num}"
        context_part += "\n"
        
        if include_arabic and chunk.get('arabic_text'):
            context_part += f"Arabic: {chunk['arabic_text'][:500]}\n"
        
        if chunk.get('english_text'):
            context_part += f"English: {chunk['english_text'][:500]}\n"
        
        context_parts.append(context_part)
    
    context = "\n".join(context_parts)
    
    # Create prompt with system context
    prompt = f"""{SYSTEM_PROMPT}

Based on the following excerpts from Bihar ul Anwar, answer the user's question.
Provide specific references (Volume, Chapter, Hadith number) whenever possible.

Context from Bihar ul Anwar:
{context}

User Question: {query}

Answer (provide detailed response with proper references):"""
    
    # Generate response
    generation_config = genai.types.GenerationConfig(
        temperature=0.7,
        max_output_tokens=2048,
    )
    
    response = CHAT_MODEL.generate_content(
        prompt,
        generation_config=generation_config
    )
    
    return response.text

# ===================== API Endpoints =====================

@app.get("/")
async def root():
    """Health check and system information"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(DISTINCT volume_number) FROM bihar_chunks")
    volumes_count = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM bihar_chunks")
    chunks_count = cursor.fetchone()[0] or 0
    
    cursor.close()
    
    return {
        "status": "healthy",
        "system": "Bihar ul Anwar RAG System",
        "volumes_processed": volumes_count,
        "total_chunks": chunks_count,
        "database": "connected",
        "gemini_api": "configured"
    }

@app.post("/query", response_model=HadithResponse, tags=["Search"])
async def search_bihar_anwar(request: QueryRequest):
    """
    Search Bihar ul Anwar for hadith and traditions
    
    This endpoint searches across all 110 volumes and returns relevant hadiths
    with proper references (Volume, Chapter, Hadith number).
    """
    import time
    start_time = time.time()
    
    try:
        # Search for relevant chunks
        chunks = search_similar_chunks(
            request.query, 
            request.top_k,
            request.volume_filter
        )
        
        if not chunks:
            return HadithResponse(
                success=False,
                query=request.query,
                answer="No relevant traditions found in Bihar ul Anwar for your query.",
                references=[],
                processing_time=time.time() - start_time,
                total_sources=0
            )
        
        # Generate comprehensive answer
        answer = generate_answer_with_context(
            request.query,
            chunks,
            request.include_arabic
        )
        
        # Format references
        references = []
        for chunk in chunks:
            metadata = chunk.get('metadata', {})
            ref = {
                'volume': chunk['volume_number'],
                'chapter': metadata.get('chapter', 'Not specified'),
                'hadith_number': metadata.get('hadith_number', 'Not specified'),
                'similarity_score': round(float(chunk['similarity']), 3),
                'excerpt_english': chunk['english_text'][:200] if chunk['english_text'] else "",
                'excerpt_arabic': chunk['arabic_text'][:200] if chunk['arabic_text'] and request.include_arabic else ""
            }
            references.append(ref)
        
        return HadithResponse(
            success=True,
            query=request.query,
            answer=answer,
            references=references,
            processing_time=time.time() - start_time,
            total_sources=len(references)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-volume", tags=["Processing"])
async def process_bihar_volume(request: ProcessingRequest):
    """
    Process a Bihar ul Anwar volume PDF
    
    This endpoint processes a single volume, extracts hadiths,
    and stores them with embeddings for search.
    """
    try:
        # Extract text and create chunks
        chunks = process_pdf_text(request.file_path, request.volume_number)
        
        if not chunks:
            return {"success": False, "message": "No text extracted from PDF"}
        
        # Generate embeddings
        texts = [chunk['full_text'] for chunk in chunks]
        embeddings = generate_embeddings(texts)
        
        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stored = 0
        for chunk, embedding in zip(chunks, embeddings):
            cursor.execute("""
                INSERT INTO bihar_chunks 
                (volume_number, chapter_name, hadith_number, arabic_text, 
                 english_text, full_text, chunk_index, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                chunk['volume_number'],
                chunk['metadata'].get('chapter'),
                chunk['metadata'].get('hadith_number'),
                chunk['arabic_text'],
                chunk['english_text'],
                chunk['full_text'],
                chunk['chunk_index'],
                embedding,
                Json(chunk['metadata'])
            ))
            stored += 1
        
        # Record processed volume
        cursor.execute("""
            INSERT INTO processed_volumes (volume_number, file_name, total_chunks)
            VALUES (%s, %s, %s)
            ON CONFLICT (volume_number) 
            DO UPDATE SET total_chunks = %s, processed_at = CURRENT_TIMESTAMP
        """, (request.volume_number, Path(request.file_path).name, stored, stored))
        
        conn.commit()
        cursor.close()
        
        return {
            "success": True,
            "message": f"Successfully processed Bihar ul Anwar Volume {request.volume_number}",
            "chunks_created": stored,
            "file": request.file_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch-process", tags=["Processing"])
async def batch_process_volumes(folder_path: str = Query(..., description="Path to folder containing Bihar ul Anwar PDFs")):
    """
    Process all Bihar ul Anwar volumes in a folder
    
    Expected naming: Volume_1.pdf, Volume_2.pdf, ..., Volume_110.pdf
    """
    folder = Path(folder_path)
    if not folder.exists():
        raise HTTPException(status_code=404, detail="Folder not found")
    
    pdf_files = list(folder.glob("*.pdf"))
    processed = []
    errors = []
    
    for pdf_file in pdf_files:
        # Extract volume number from filename
        match = re.search(r'(\d+)', pdf_file.stem)
        if not match:
            errors.append(f"Cannot determine volume number for {pdf_file.name}")
            continue
        
        volume_num = int(match.group(1))
        
        try:
            chunks = process_pdf_text(str(pdf_file), volume_num)
            texts = [chunk['full_text'] for chunk in chunks]
            embeddings = generate_embeddings(texts)
            
            # Store in database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            for chunk, embedding in zip(chunks, embeddings):
                cursor.execute("""
                    INSERT INTO bihar_chunks 
                    (volume_number, chapter_name, hadith_number, arabic_text, 
                     english_text, full_text, chunk_index, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    chunk['volume_number'],
                    chunk['metadata'].get('chapter'),
                    chunk['metadata'].get('hadith_number'),
                    chunk['arabic_text'],
                    chunk['english_text'],
                    chunk['full_text'],
                    chunk['chunk_index'],
                    embedding,
                    Json(chunk['metadata'])
                ))
            
            conn.commit()
            cursor.close()
            
            processed.append(f"Volume {volume_num}: {len(chunks)} chunks")
            
        except Exception as e:
            errors.append(f"Volume {volume_num}: {str(e)}")
    
    return {
        "success": True,
        "processed": processed,
        "errors": errors,
        "total_processed": len(processed),
        "total_errors": len(errors)
    }

@app.get("/volumes", tags=["Information"])
async def list_processed_volumes():
    """List all processed Bihar ul Anwar volumes"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT 
            volume_number,
            COUNT(*) as chunk_count,
            COUNT(DISTINCT chapter_name) as chapters,
            MIN(created_at) as processed_date
        FROM bihar_chunks
        GROUP BY volume_number
        ORDER BY volume_number
    """)
    
    volumes = cursor.fetchall()
    cursor.close()
    
    return {
        "total_volumes": len(volumes),
        "volumes": volumes,
        "missing_volumes": [i for i in range(1, 111) if i not in [v['volume_number'] for v in volumes]]
    }

@app.get("/search-by-reference", tags=["Search"])
async def search_by_reference(
    volume: int = Query(..., ge=1, le=110, description="Volume number"),
    chapter: Optional[str] = Query(None, description="Chapter number"),
    hadith: Optional[str] = Query(None, description="Hadith number")
):
    """Search for specific hadith by reference (Volume, Chapter, Hadith number)"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    query = "SELECT * FROM bihar_chunks WHERE volume_number = %s"
    params = [volume]
    
    if chapter:
        query += " AND (metadata->>'chapter' = %s OR chapter_name = %s)"
        params.extend([chapter, chapter])
    
    if hadith:
        query += " AND (metadata->>'hadith_number' = %s OR hadith_number = %s)"
        params.extend([hadith, hadith])
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    
    return {
        "success": True,
        "query": f"Volume {volume}, Chapter {chapter or 'Any'}, Hadith {hadith or 'Any'}",
        "results": results,
        "count": len(results)
    }

@app.get("/statistics", tags=["Information"])
async def get_statistics():
    """Get Bihar ul Anwar database statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total statistics
    cursor.execute("SELECT COUNT(DISTINCT volume_number) FROM bihar_chunks")
    stats['total_volumes'] = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM bihar_chunks")
    stats['total_chunks'] = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(DISTINCT chapter_name) FROM bihar_chunks WHERE chapter_name IS NOT NULL")
    stats['total_chapters'] = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(DISTINCT hadith_number) FROM bihar_chunks WHERE hadith_number IS NOT NULL")
    stats['total_hadiths'] = cursor.fetchone()[0] or 0
    
    # Language distribution
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN arabic_text != '' THEN 1 END) as with_arabic,
            COUNT(CASE WHEN english_text != '' THEN 1 END) as with_english
        FROM bihar_chunks
    """)
    lang_stats = cursor.fetchone()
    stats['chunks_with_arabic'] = lang_stats[0] or 0
    stats['chunks_with_english'] = lang_stats[1] or 0
    
    cursor.close()
    
    return {
        "success": True,
        "statistics": stats,
        "coverage": f"{stats['total_volumes']}/110 volumes processed"
    }

# ===================== Startup Event =====================
# @app.on_event("startup")
# async def startup_event():
#     """Initialize database on startup"""
#     try:
#         init_database()
#         print("✅ Bihar ul Anwar RAG System started")
#         print("📖 Access Swagger UI at: http://localhost:8000/docs")
#     except Exception as e:
#         print(f"❌ Startup failed: {e}")

# @app.on_event("shutdown")
# async def shutdown_event():
#     """Cleanup on shutdown"""
#     global db_conn
#     if db_conn:
#         db_conn.close()
#         print("Database connection closed")

# ===================== Run Server =====================
if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Bihar ul Anwar RAG System...")
    print("📚 System designed for 110 volumes of Bihar ul Anwar")
    print("🔍 Swagger UI will be available at: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )