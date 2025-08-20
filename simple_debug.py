# simple_debug.py - Quick test and fix
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db_connection
import psycopg2
from psycopg2.extras import RealDictCursor

def simple_test():
    """Simple test to see what's wrong"""
    print("🔍 SIMPLE REFERENCE SEARCH TEST")
    print("=" * 40)
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Test 1: Basic query without filters
        print("Test 1: Basic Volume 1, Chapter 1 query")
        cursor.execute("""
            SELECT 
                volume_number,
                chapter_name,
                hadith_number,
                LEFT(full_text, 150) as text_preview
            FROM bihar_chunks 
            WHERE volume_number = 1 AND chapter_name = '1'
            ORDER BY chunk_index
            LIMIT 5
        """)
        
        basic_results = cursor.fetchall()
        print(f"   Found {len(basic_results)} basic results")
        
        for i, result in enumerate(basic_results, 1):
            print(f"   {i}. Vol {result['volume_number']}, Ch {result['chapter_name']}, H {result['hadith_number']}")
            print(f"      Text: {result['text_preview']}...")
            print()
        
        # Test 2: Test with length filter
        print("Test 2: With length filter")
        cursor.execute("""
            SELECT 
                volume_number,
                chapter_name,
                hadith_number,
                LEFT(full_text, 150) as text_preview
            FROM bihar_chunks 
            WHERE volume_number = 1 
            AND chapter_name = '1'
            AND LENGTH(COALESCE(english_text, full_text, '')) > 80
            LIMIT 5
        """)
        
        filtered_results = cursor.fetchall()
        print(f"   Found {len(filtered_results)} results with length filter")
        
        for i, result in enumerate(filtered_results, 1):
            print(f"   {i}. Vol {result['volume_number']}, Ch {result['chapter_name']}, H {result['hadith_number']}")
            print(f"      Text: {result['text_preview']}...")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()

def test_function_call():
    """Test our actual function"""
    print("\n🔍 TESTING ACTUAL FUNCTION")
    print("=" * 40)
    
    try:
        from database import search_by_reference_relaxed
        results = search_by_reference_relaxed(1, "1", None)
        print(f"Function returned: {len(results)} results")
        
        for i, result in enumerate(results[:3], 1):
            print(f"   {i}. Vol {result['volume_number']}, Ch {result['chapter_name']}")
            print(f"      Text: {result['full_text'][:100]}...")
            
    except Exception as e:
        print(f"❌ Function error: {e}")
        import traceback
        traceback.print_exc()

def main():
    simple_test()
    test_function_call()

if __name__ == "__main__":
    main()