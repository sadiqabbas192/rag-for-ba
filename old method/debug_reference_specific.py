# debug_reference_specific.py - Debug the exact reference search issue
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db_connection
import psycopg2
from psycopg2.extras import RealDictCursor

def debug_reference_search_step_by_step():
    """Debug reference search step by step"""
    print("🔍 DEBUGGING REFERENCE SEARCH STEP BY STEP")
    print("=" * 60)
    
    volume = 1
    chapter = "1"
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Step 1: Check raw data exists
        print("Step 1: Check if data exists")
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM bihar_chunks 
            WHERE volume_number = %s
        """, [volume])
        
        total = cursor.fetchone()['total']
        print(f"   Total chunks in Volume {volume}: {total}")
        
        # Step 2: Check chapter data exists
        print("\nStep 2: Check chapter data")
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM bihar_chunks 
            WHERE volume_number = %s AND chapter_name = %s
        """, [volume, chapter])
        
        chapter_total = cursor.fetchone()['total']
        print(f"   Chunks with Chapter {chapter}: {chapter_total}")
        
        # Step 3: Check what chapter values exist
        print("\nStep 3: Available chapter values")
        cursor.execute("""
            SELECT DISTINCT chapter_name, COUNT(*) as count
            FROM bihar_chunks 
            WHERE volume_number = %s AND chapter_name IS NOT NULL
            GROUP BY chapter_name
            ORDER BY chapter_name
            LIMIT 10
        """, [volume])
        
        chapters = cursor.fetchall()
        print(f"   Available chapters: {[(ch['chapter_name'], ch['count']) for ch in chapters]}")
        
        # Step 4: Test the exact query from our function
        print("\nStep 4: Test exact query from function")
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
            AND LENGTH(COALESCE(english_text, full_text, '')) > 80
            AND (chapter_name = %s OR chapter_name ILIKE %s)
            ORDER BY 
                CASE WHEN hadith_number IS NOT NULL THEN 1 ELSE 2 END,
                CASE WHEN english_text ILIKE '%said%' OR english_text ILIKE '%narrated%' THEN 1 ELSE 2 END,
                chunk_index 
            LIMIT 25
        """
        
        params = [volume, chapter, f'%{chapter}%']
        cursor.execute(base_query, params)
        raw_results = cursor.fetchall()
        
        print(f"   Raw query results: {len(raw_results)}")
        
        for i, result in enumerate(raw_results[:5], 1):
            print(f"   {i}. Vol {result['volume_number']}, Ch {result['chapter_name']}, H {result['hadith_number']}")
            print(f"      Text: {result['full_text'][:100]}...")
        
        # Step 5: Test the filtering logic
        print("\nStep 5: Test filtering logic")
        filtered_results = []
        for result in raw_results:
            full_text = result['full_text'].lower().strip()
            english_text = result.get('english_text', '').lower()
            
            # Check our exclusion patterns
            should_exclude = (
                ('table of contents' in full_text and len(full_text) < 200)
                or
                (full_text.startswith('bihar al-anwaar') and len(full_text) < 100)
                or
                (full_text.startswith('overall') and 'index' in full_text)
                or
                (len(full_text.strip()) < 60)
            )
            
            if not should_exclude:
                # Add quality score
                quality_score = 0
                if result.get('hadith_number'):
                    quality_score += 2
                if any(word in english_text for word in ['said', 'narrated', 'reported', 'tradition']):
                    quality_score += 2
                if len(english_text) > 100:
                    quality_score += 1
                
                result['quality_score'] = quality_score
                filtered_results.append(result)
                
                print(f"   INCLUDED: Vol {result['volume_number']}, Ch {result['chapter_name']}, Score {quality_score}")
                print(f"      Text: {result['full_text'][:80]}...")
            else:
                print(f"   EXCLUDED: {result['full_text'][:80]}...")
        
        print(f"\nFinal filtered results: {len(filtered_results)}")
        
        # Step 6: Check if our function would return these
        if filtered_results:
            print("\nStep 6: Our function should return these results")
            for i, result in enumerate(filtered_results[:5], 1):
                print(f"   {i}. Vol {result['volume_number']}, Ch {result['chapter_name']}, H {result['hadith_number']}")
        else:
            print("\nStep 6: No results would be returned - checking why...")
            
            # Debug why filtering failed
            print("   Debugging exclusion reasons:")
            for result in raw_results[:3]:
                full_text = result['full_text'].lower().strip()
                print(f"   Text: {full_text[:100]}...")
                print(f"   Length: {len(full_text)}")
                print(f"   Has 'table of contents': {'table of contents' in full_text}")
                print(f"   Starts with 'bihar al-anwaar': {full_text.startswith('bihar al-anwaar')}")
                print(f"   Has 'overall' and 'index': {full_text.startswith('overall') and 'index' in full_text}")
                print(f"   Too short: {len(full_text.strip()) < 60}")
                print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()

def main():
    debug_reference_search_step_by_step()

if __name__ == "__main__":
    main()