# database.py - Database Functions and Models
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from pgvector.psycopg2 import register_vector
from typing import List, Dict, Optional
from config import DB_CONFIG

# Database connection pool
db_conn = None

def get_db_connection():
    """Get or create database connection"""
    global db_conn
    if db_conn is None or db_conn.closed:
        db_conn = psycopg2.connect(**DB_CONFIG)
        register_vector(db_conn)
    return db_conn

def init_database():
    """Initialize database tables with proper error handling"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create pgvector extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        
        # Create main table
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes separately
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bihar_volume 
            ON bihar_chunks (volume_number)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bihar_hadith 
            ON bihar_chunks (hadith_number)
        """)
        
        # Vector index (create only if table has data)
        cursor.execute("SELECT COUNT(*) FROM bihar_chunks")
        count = cursor.fetchone()[0]
        
        if count > 100:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bihar_embedding 
                ON bihar_chunks 
                USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100)
            """)
        
        # Processed volumes table
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
        print("✅ Database initialized successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Database initialization error: {e}")
        raise
    finally:
        cursor.close()

def batch_insert_chunks(chunks_data: List[Dict], batch_size: int = 50):
    """Optimized batch insertion"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        total_chunks = len(chunks_data)
        print(f"Inserting {total_chunks} chunks in batches of {batch_size}")
        
        inserted_count = 0
        for i in range(0, total_chunks, batch_size):
            batch = chunks_data[i:i + batch_size]
            
            for chunk in batch:
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
                    chunk['embedding'],
                    Json(chunk['metadata'])
                ))
                inserted_count += 1
            
            # Commit each batch
            conn.commit()
            print(f"  Inserted batch: {inserted_count}/{total_chunks}")
        
        return inserted_count
        
    except Exception as e:
        conn.rollback()
        print(f"Batch insert error: {e}")
        raise
    finally:
        cursor.close()

def search_similar_chunks(query_embedding: List[float], top_k: int = 7, volume_filter: Optional[int] = None) -> List[Dict]:
    """Search for similar chunks using vector similarity - FIXED VERSION"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Check if embedding is valid
        if not query_embedding or all(x == 0.0 for x in query_embedding):
            print("❌ Invalid query embedding (all zeros)")
            return []
        
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
            WHERE embedding IS NOT NULL
        """
        
        params = [query_embedding]
        
        # Add volume filter if specified
        if volume_filter:
            base_query += " AND volume_number = %s"
            params.append(volume_filter)
        
        # Add similarity threshold and ordering
        base_query += """
            AND 1 - (embedding <=> %s::vector) > 0.2
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        params.extend([query_embedding, query_embedding, top_k])
        
        cursor.execute(base_query, params)
        results = cursor.fetchall()
        
        return results
        
    except Exception as e:
        print(f"❌ Vector search error: {e}")
        return []
    finally:
        cursor.close()

def get_database_stats():
    """Get comprehensive database statistics"""
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
    return stats

def get_processed_volumes():
    """Get list of processed volumes"""
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
    
    return volumes

def search_by_reference(volume: int, chapter: Optional[str] = None, hadith: Optional[str] = None):
    """Search for specific hadith by reference - FIXED VERSION"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Base query
        query = "SELECT * FROM bihar_chunks WHERE volume_number = %s"
        params = [volume]
        
        # Add chapter filter if provided
        if chapter:
            # Try both metadata and direct chapter_name
            query += """ AND (
                (metadata->>'chapter' = %s) OR 
                (chapter_name = %s) OR
                (chapter_name ILIKE %s)
            )"""
            params.extend([chapter, chapter, f"%{chapter}%"])
        
        # Add hadith filter if provided  
        if hadith:
            # Try both metadata and direct hadith_number
            query += """ AND (
                (metadata->>'hadith_number' = %s) OR 
                (hadith_number = %s) OR
                (hadith_number ILIKE %s)
            )"""
            params.extend([hadith, hadith, f"%{hadith}%"])
        
        # Add ordering and limit
        query += " ORDER BY chunk_index LIMIT 50"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        return results
        
    except Exception as e:
        print(f"❌ Database error in search_by_reference: {e}")
        return []
    finally:
        cursor.close()

def record_processed_volume(volume_number: int, file_name: str, total_chunks: int):
    """Record a successfully processed volume"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO processed_volumes (volume_number, file_name, total_chunks)
        VALUES (%s, %s, %s)
        ON CONFLICT (volume_number) 
        DO UPDATE SET 
            total_chunks = EXCLUDED.total_chunks,
            processed_at = CURRENT_TIMESTAMP,
            file_name = EXCLUDED.file_name
    """, (volume_number, file_name, total_chunks))
    
    conn.commit()
    cursor.close()

def close_db_connection():
    """Close database connection"""
    global db_conn
    if db_conn and not db_conn.closed:
        db_conn.close()
        print("Database connection closed")