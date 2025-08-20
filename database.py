# database.py - Complete database functions with enhancements
import psycopg2
import re
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

def search_similar_chunks_relaxed(query_embedding: List[float], top_k: int = 7, volume_filter: Optional[int] = None) -> List[Dict]:
    """IMPROVED: Vector search with smart content filtering"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Check if embedding is valid
        if not query_embedding or all(x == 0.0 for x in query_embedding):
            print("❌ Invalid query embedding")
            return []
        
        # Query with reasonable similarity threshold
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
            AND LENGTH(COALESCE(english_text, full_text, '')) > 100
        """
        
        params = [query_embedding]
        
        # Add volume filter
        if volume_filter:
            base_query += " AND volume_number = %s"
            params.append(volume_filter)
        
        # Reasonable similarity threshold
        base_query += """
            AND 1 - (embedding <=> %s::vector) > 0.3
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        params.extend([query_embedding, query_embedding, top_k * 3])  # Get more to filter
        
        cursor.execute(base_query, params)
        raw_results = cursor.fetchall()
        
        print(f"🔍 Found {len(raw_results)} raw results")
        
        # IMPROVED: Smart filtering that keeps actual content
        filtered_results = []
        for result in raw_results:
            full_text = result['full_text'].lower().strip()
            english_text = result.get('english_text', '').lower()
            
            # Skip obvious non-content
            should_exclude = (
                # Table of contents entries
                ('table of contents' in full_text and len(full_text) < 200)
                or
                # Pure index pages
                (full_text.startswith('overall') and 'index' in full_text and len(full_text) < 150)
                or
                # Very short page headers
                (len(full_text) < 80 and 'bihar al-anwaar' in full_text)
                or
                # Chapter titles without content (short)
                (full_text.startswith('chapter') and len(full_text) < 120)
            )
            
            # Prefer content with hadith indicators
            has_hadith_content = any([
                'said' in english_text,
                'narrated' in english_text,
                'reported' in english_text,
                'tradition' in english_text,
                'hadith' in english_text,
                result.get('hadith_number') is not None,
                'قال' in result.get('arabic_text', ''),
                'عن' in result.get('arabic_text', ''),
            ])
            
            if not should_exclude:
                # Prioritize hadith content
                result['content_priority'] = 1 if has_hadith_content else 0.5
                filtered_results.append(result)
        
        # Sort by content priority and similarity
        filtered_results.sort(key=lambda x: (x['content_priority'], x['similarity']), reverse=True)
        
        # Return top results
        final_results = filtered_results[:top_k]
        
        print(f"🔍 Smart filtering: {len(final_results)} quality results from {len(raw_results)} raw results")
        return final_results
        
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

def search_by_reference_relaxed(volume: int, chapter: Optional[str] = None, hadith: Optional[str] = None):
    """FIXED: Reference search with corrected SQL"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        print(f"🔍 Fixed search: Volume {volume}, Chapter {chapter}, Hadith {hadith}")
        
        # Start with base query
        base_query = """
            SELECT 
                volume_number,
                chapter_name,
                hadith_number,
                arabic_text,
                english_text,
                LEFT(full_text, 300) as full_text,
                metadata
            FROM bihar_chunks 
            WHERE volume_number = %s
        """
        params = [volume]
        
        # Add chapter filter if provided
        if chapter and chapter.strip():
            base_query += " AND (chapter_name = %s OR chapter_name ILIKE %s)"
            params.append(chapter)
            params.append(f'%{chapter}%')
        
        # Add hadith filter if provided  
        if hadith and hadith.strip():
            base_query += " AND (hadith_number = %s OR hadith_number ILIKE %s)"
            params.append(hadith)
            params.append(f'%{hadith}%')
        
        # Add basic length filter and ordering
        base_query += """
            AND LENGTH(COALESCE(english_text, full_text, '')) > 50
            ORDER BY 
                CASE WHEN hadith_number IS NOT NULL THEN 1 ELSE 2 END,
                chunk_index 
            LIMIT 20
        """
        
        print(f"Executing query with {len(params)} parameters...")
        print(f"Query: {base_query}")
        print(f"Params: {params}")
        
        cursor.execute(base_query, params)
        raw_results = cursor.fetchall()
        
        print(f"Raw results: {len(raw_results)}")
        
        # Very minimal filtering - only exclude obvious non-content
        filtered_results = []
        for result in raw_results:
            full_text = result['full_text'].lower().strip() if result['full_text'] else ""
            
            # Only exclude very obvious non-content
            should_exclude = (
                len(full_text) < 30  # Very short
                or full_text.startswith('table of contents')  # Pure TOC
                or (full_text.startswith('page ') and len(full_text) < 50)  # Page numbers only
            )
            
            if not should_exclude:
                filtered_results.append(result)
        
        print(f"✅ Found {len(filtered_results)} results after minimal filtering")
        return filtered_results
        
    except Exception as e:
        print(f"❌ Fixed reference search error: {e}")
        import traceback
        traceback.print_exc()
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

# Additional helper functions remain the same
def analyze_volume_metadata(volume: int):
    """Analyze metadata structure for a volume"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                chapter_name,
                hadith_number,
                metadata,
                LEFT(full_text, 200) as text_sample
            FROM bihar_chunks 
            WHERE volume_number = %s 
            ORDER BY chunk_index
            LIMIT 10
        """, [volume])
        
        results = cursor.fetchall()
        
        chapters_found = set()
        hadiths_found = set()
        
        for row in results:
            if row['chapter_name']:
                chapters_found.add(row['chapter_name'])
            if row['hadith_number']:
                hadiths_found.add(row['hadith_number'])
        
        return {
            'chapters': list(chapters_found),
            'hadiths': list(hadiths_found)
        }
        
    except Exception as e:
        print(f"❌ Error analyzing metadata: {e}")
        return {}
    finally:
        cursor.close()