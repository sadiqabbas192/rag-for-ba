# main.py - Bihar ul Anwar RAG System (Updated with correct imports)
import time
from typing import List, Dict, Optional, Any
from pathlib import Path
from contextlib import asynccontextmanager

# FastAPI
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Local imports - UPDATED FOR NEW FUNCTION NAMES
from config import DB_BATCH_SIZE
from database import (
    init_database, 
    get_database_stats, 
    get_processed_volumes, 
    search_by_reference_relaxed,      # Make sure this matches
    search_similar_chunks_relaxed,    # Make sure this matches
    batch_insert_chunks,
    record_processed_volume,
    close_db_connection
)

from processing import (
    process_pdf_text,
    generate_embeddings,
    generate_query_embedding,
    generate_answer_with_context  # This function is enhanced but keeps same name
)

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
    # Startup
    print("🚀 Starting Enhanced Bihar ul Anwar RAG System...")
    print("📚 System designed for 110 volumes of Bihar ul Anwar")
    print("🔍 Swagger UI will be available at: http://localhost:8000/docs")
    
    try:
        init_database()
        print("✅ Enhanced Bihar ul Anwar RAG System started")
        print("📖 Access Swagger UI at: http://localhost:8000/docs")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
    
    yield
    
    # Shutdown
    close_db_connection()
    print("📚 Shutting down...")

app = FastAPI(
    title="Enhanced Bihar ul Anwar RAG System",
    description="""
    ## Enhanced Search System for Bihar ul Anwar (110 Volumes)
    
    This API provides intelligent search and retrieval from all 110 volumes of Bihar ul Anwar,
    with enhanced filtering and content quality controls.
    
    ### Enhanced Features:
    - Search across all 110 volumes with content filtering
    - Bilingual support (Arabic + English) 
    - Precise hadith referencing (Volume, Chapter, Hadith number)
    - Enhanced AI responses using only book content
    - Improved vector similarity search
    - Quality-based content ranking
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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

# ===================== API Endpoints =====================

@app.get("/")
async def root():
    """Health check and system information"""
    stats = get_database_stats()
    
    return {
        "status": "healthy",
        "system": "Enhanced Bihar ul Anwar RAG System",
        "version": "2.0.0",
        "volumes_processed": stats['total_volumes'],
        "total_chunks": stats['total_chunks'],
        "database": "connected",
        "gemini_api": "configured",
        "enhancements": [
            "Content filtering",
            "Enhanced AI prompts", 
            "Quality-based ranking",
            "Improved reference extraction"
        ]
    }

@app.post("/query", response_model=HadithResponse, tags=["Search"])
async def search_bihar_anwar(request: QueryRequest):
    """
    Enhanced Search Bihar ul Anwar for hadith and traditions
    
    This endpoint searches across all 110 volumes with enhanced filtering
    and returns relevant hadiths with improved accuracy.
    """
    start_time = time.time()
    
    try:
        # Generate query embedding
        query_embedding = generate_query_embedding(request.query)
        
        # Enhanced search for relevant chunks
        chunks = search_similar_chunks_relaxed(
            query_embedding, 
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
        
        # Generate enhanced answer with strict content controls
        answer = generate_answer_with_context(
            request.query,
            chunks,
            request.include_arabic
        )
        
        # Format references with clean format
        references = []
        for chunk in chunks:
            metadata = chunk.get('metadata', {})
            
            # Build clean reference
            ref_parts = [f"Volume {chunk['volume_number']}"]
            if metadata.get('chapter'):
                ref_parts.append(f"Chapter {metadata['chapter']}")
            if metadata.get('hadith_number'):
                ref_parts.append(f"Hadith {metadata['hadith_number']}")
            
            ref = {
                'volume': chunk['volume_number'],
                'chapter': metadata.get('chapter', 'Not specified'),
                'hadith_number': metadata.get('hadith_number', 'Not specified'),
                'similarity_score': round(float(chunk['similarity']), 3),
                'reference': f"Bihar ul Anwar, {', '.join(ref_parts)}",
                'excerpt_english': chunk['english_text'][:150] if chunk['english_text'] else "",
                'excerpt_arabic': chunk['arabic_text'][:150] if chunk['arabic_text'] and request.include_arabic else ""
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
    """Process a Bihar ul Anwar volume PDF with enhanced metadata extraction"""
    start_time = time.time()
    
    try:
        print(f"\n📖 Processing Volume {request.volume_number} (Enhanced)")
        print(f"🔍 File: {request.file_path}")
        
        # Extract text and create chunks
        chunks = process_pdf_text(request.file_path, request.volume_number, max_pages=100)
        
        if not chunks:
            return {"success": False, "message": "No text extracted from PDF"}
        
        print(f"📝 Created {len(chunks)} text chunks")
        
        # Generate embeddings
        texts = [chunk['full_text'] for chunk in chunks]
        embeddings = generate_embeddings(texts, batch_size=2)
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding
        
        # Batch insert to database
        stored = batch_insert_chunks(chunks, batch_size=DB_BATCH_SIZE)
        
        # Record processed volume
        record_processed_volume(
            request.volume_number, 
            Path(request.file_path).name, 
            stored
        )
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "message": f"Successfully processed Bihar ul Anwar Volume {request.volume_number}",
            "chunks_created": stored,
            "processing_time": processing_time,
            "pages_processed": "Max 100 pages (optimized)",
            "file": request.file_path,
            "enhancements": "Enhanced metadata extraction applied"
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        print(f"❌ Volume {request.volume_number} failed: {error_msg}")
        
        return {
            "success": False,
            "message": f"Failed to process Volume {request.volume_number}",
            "error": error_msg,
            "processing_time": processing_time
        }

@app.get("/volumes", tags=["Information"])
async def list_processed_volumes():
    """List all processed Bihar ul Anwar volumes"""
    volumes = get_processed_volumes()
    
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
    """Enhanced search for specific hadith by reference with content filtering"""
    try:
        results = search_by_reference_relaxed(volume, chapter, hadith)
        
        # Format results with clean references
        formatted_results = []
        for result in results:
            # Build clean reference
            ref_parts = [f"Volume {result['volume_number']}"]
            if result.get('chapter_name'):
                ref_parts.append(f"Chapter {result['chapter_name']}")
            if result.get('hadith_number'):
                ref_parts.append(f"Hadith {result['hadith_number']}")
            
            formatted_result = dict(result)
            formatted_result['clean_reference'] = f"Bihar ul Anwar, {', '.join(ref_parts)}"
            formatted_results.append(formatted_result)
        
        return {
            "success": True,
            "query": f"Volume {volume}, Chapter {chapter or 'Any'}, Hadith {hadith or 'Any'}",
            "results": formatted_results,
            "count": len(formatted_results),
            "enhancement": "Content filtered and quality ranked"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "count": 0
        }

@app.get("/statistics", tags=["Information"])
async def get_statistics():
    """Get enhanced Bihar ul Anwar database statistics"""
    stats = get_database_stats()
    
    return {
        "success": True,
        "statistics": stats,
        "coverage": f"{stats['total_volumes']}/110 volumes processed",
        "quality_metrics": {
            "chapters_extracted": f"{stats['total_chapters']} unique chapters",
            "hadiths_extracted": f"{stats['total_hadiths']} unique hadiths",
            "bilingual_support": f"{stats['chunks_with_arabic']} Arabic, {stats['chunks_with_english']} English"
        }
    }

# ===================== Run Server =====================
if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Enhanced Bihar ul Anwar RAG System...")
    print("📚 System designed for 110 volumes of Bihar ul Anwar")
    print("🔍 Enhanced with content filtering and quality controls")
    print("📖 Swagger UI will be available at: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )