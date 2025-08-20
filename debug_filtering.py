# debug_filtering.py - Debug the filtering issues
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db_connection
from processing import generate_query_embedding
import psycopg2
from psycopg2.extras import RealDictCursor

def debug_query_embedding():
    """Debug query embedding generation"""
    print("🔍 DEBUGGING QUERY EMBEDDING")
    print("=" * 50)
    
    query = "What does Chapter 1 of Volume 1 say about knowledge?"
    
    try:
        embedding = generate_query_embedding(query)
        
        print(f"Query: {query}")
        print(f"Embedding length: {len(embedding)}")
        print(f"Embedding type: {type(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
        print(f"All zeros?: {all(x == 0.0 for x in embedding)}")
        
        if all(x == 0.0 for x in embedding):
            print("❌ PROBLEM: Query embedding is all zeros!")
        else:
            print("✅ Query embedding looks good")
            
        return embedding
        
    except Exception as e:
        print(f"❌ Error generating query embedding: {e}")
        return None

def debug_database_search(query_embedding):
    """Debug database search without filters"""
    print("\n🔍 DEBUGGING DATABASE SEARCH")
    print("=" * 50)
    
    if not query_embedding or all(x == 0.0 for x in query_embedding):
        print("❌ Cannot test with invalid embedding")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Test 1: Basic similarity search without filters
        print("Test 1: Basic similarity search")
        cursor.execute("""
            SELECT 
                volume_number,
                chapter_name,
                hadith_number,
                LEFT(english_text, 100) as text_preview,
                1 - (embedding <=> %s::vector) as similarity
            FROM bihar_chunks
            WHERE embedding IS NOT NULL
            AND volume_number = 1
            ORDER BY embedding <=> %s::vector
            LIMIT 5
        """, [query_embedding, query_embedding])
        
        basic_results = cursor.fetchall()
        print(f"   Found {len(basic_results)} results")
        
        for i, result in enumerate(basic_results, 1):
            print(f"   {i}. Vol {result['volume_number']}, Ch {result['chapter_name']}, "
                  f"Sim: {result['similarity']:.3f}")
            print(f"      Text: {result['text_preview']}...")
        
        # Test 2: Check similarity thresholds
        print("\nTest 2: Similarity distribution")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN 1 - (embedding <=> %s::vector) > 0.5 THEN 1 END) as above_50,
                COUNT(CASE WHEN 1 - (embedding <=> %s::vector) > 0.3 THEN 1 END) as above_30,
                COUNT(CASE WHEN 1 - (embedding <=> %s::vector) > 0.25 THEN 1 END) as above_25,
                COUNT(CASE WHEN 1 - (embedding <=> %s::vector) > 0.2 THEN 1 END) as above_20
            FROM bihar_chunks
            WHERE embedding IS NOT NULL AND volume_number = 1
        """, [query_embedding, query_embedding, query_embedding, query_embedding])
        
        threshold_stats = cursor.fetchone()
        print(f"   Total chunks: {threshold_stats['total']}")
        print(f"   Above 0.5 similarity: {threshold_stats['above_50']}")
        print(f"   Above 0.3 similarity: {threshold_stats['above_30']}")
        print(f"   Above 0.25 similarity: {threshold_stats['above_25']}")
        print(f"   Above 0.2 similarity: {threshold_stats['above_20']}")
        
        # Test 3: Check Chapter 1 content specifically
        print("\nTest 3: Chapter 1 content check")
        cursor.execute("""
            SELECT 
                id,
                chapter_name,
                hadith_number,
                LEFT(english_text, 150) as text_preview,
                CASE 
                    WHEN full_text ILIKE '%table of contents%' THEN 'TOC'
                    WHEN full_text ILIKE '%index%' THEN 'INDEX'
                    WHEN english_text ILIKE '%said%' OR english_text ILIKE '%narrated%' THEN 'HADITH'
                    ELSE 'OTHER'
                END as content_type
            FROM bihar_chunks
            WHERE volume_number = 1 AND chapter_name = '1'
            ORDER BY chunk_index
            LIMIT 10
        """)
        
        chapter_results = cursor.fetchall()
        print(f"   Found {len(chapter_results)} Chapter 1 results")
        
        for i, result in enumerate(chapter_results, 1):
            print(f"   {i}. ID {result['id']}, Ch {result['chapter_name']}, "
                  f"Type: {result['content_type']}")
            print(f"      Text: {result['text_preview']}...")
        
    except Exception as e:
        print(f"❌ Database search error: {e}")
    finally:
        cursor.close()

def debug_reference_search():
    """Debug reference search filters"""
    print("\n🔍 DEBUGGING REFERENCE SEARCH FILTERS")
    print("=" * 50)
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Test without any content filtering
        print("Test 1: Reference search without content filters")
        cursor.execute("""
            SELECT 
                volume_number,
                chapter_name,
                hadith_number,
                LEFT(full_text, 150) as text_preview
            FROM bihar_chunks 
            WHERE volume_number = 1 AND chapter_name = '1'
            ORDER BY chunk_index
            LIMIT 10
        """)
        
        raw_results = cursor.fetchall()
        print(f"   Raw results: {len(raw_results)}")
        
        for i, result in enumerate(raw_results, 1):
            text_lower = result['text_preview'].lower()
            
            # Check against exclusion patterns
            exclude_patterns = [
                'table of contents',
                'overall index',
                'bihar al-anwaar volume',
                'page \\d+ of \\d+',
            ]
            
            excluded = False
            for pattern in exclude_patterns:
                import re
                if re.search(pattern, text_lower, re.IGNORECASE):
                    excluded = True
                    print(f"   {i}. EXCLUDED by '{pattern}': {result['text_preview'][:100]}...")
                    break
            
            if not excluded:
                print(f"   {i}. INCLUDED: {result['text_preview'][:100]}...")
        
    except Exception as e:
        print(f"❌ Reference search debug error: {e}")
    finally:
        cursor.close()

def main():
    """Run all debugging tests"""
    print("🔧 BIHAR UL ANWAR FILTERING DEBUG")
    print("=" * 60)
    
    # Step 1: Debug query embedding
    embedding = debug_query_embedding()
    
    # Step 2: Debug database search
    if embedding:
        debug_database_search(embedding)
    
    # Step 3: Debug reference search
    debug_reference_search()
    
    print(f"\n💡 RECOMMENDATIONS:")
    print("1. If embedding is all zeros -> Fix API key/model")
    print("2. If similarity too low -> Reduce threshold from 0.25 to 0.1")
    print("3. If all content excluded -> Relax filtering patterns")
    print("4. If no Chapter 1 content -> Fix metadata extraction")

if __name__ == "__main__":
    main()