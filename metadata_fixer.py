# metadata_fixer.py - Comprehensive fix for null metadata in existing chunks
import sys
import os
import re
from typing import Dict, List, Tuple, Optional
import psycopg2
from psycopg2.extras import RealDictCursor, Json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import get_db_connection

class MetadataExtractor:
    """Advanced metadata extraction for Bihar ul Anwar chunks"""
    
    def __init__(self):
        self.chapter_patterns = [
            # English patterns
            r'chapter\s+(\d+)',
            r'ch\.?\s*(\d+)',
            r'section\s+(\d+)',
            
            # Arabic patterns  
            r'باب\s+(\d+)',
            r'الباب\s+(\d+)',
            r'فصل\s+(\d+)',
            
            # Mixed patterns
            r'(?:chapter|ch\.?|باب|الباب)\s*[-–—:]*\s*(\d+)',
            
            # Table of contents patterns
            r'(\d+)\s*[-–—.]\s*(?:the\s+)?(?:chapter|book|باب)',
            r'chapter\s+(\d+)\s*[-–—:]',
        ]
        
        self.hadith_patterns = [
            # English patterns
            r'hadith\s+#?(\d+)',
            r'tradition\s+#?(\d+)', 
            r'narration\s+#?(\d+)',
            r'h\.?\s*(\d+)',
            r'tradition\s+no\.?\s*(\d+)',
            
            # Arabic patterns
            r'حديث\s+(\d+)',
            r'رواية\s+(\d+)',
            r'خبر\s+(\d+)',
            
            # Mixed patterns
            r'(?:hadith|tradition|حديث|رواية)\s*[-–—:#]*\s*(\d+)',
            
            # Numbered list patterns
            r'^\s*(\d+)\s*[-–—.]\s*(?:من|عن|قال)',
            r'^\s*(\d+)\s*[-–—.]\s*[A-Z][a-z]+.*(?:said|narrated)',
        ]
        
        self.exclusion_patterns = [
            r'page\s+\d+',
            r'volume\s+\d+', 
            r'www\.hubeali\.com',
            r'bihar\s+al-anwaar',
            r'table\s+of\s+contents',
            r'index',
            r'فهرست',
        ]

    def extract_metadata_advanced(self, text: str, volume_num: int) -> Dict:
        """Extract metadata using multiple strategies"""
        
        metadata = {
            'volume': volume_num,
            'chapter': None,
            'hadith_number': None,
            'extraction_method': None,
            'confidence': 0
        }
        
        if not text or len(text.strip()) < 20:
            return metadata
        
        # Clean text for analysis
        clean_text = self._clean_text_for_extraction(text)
        
        # Strategy 1: Look for clear chapter headers
        chapter = self._extract_chapter_advanced(clean_text)
        if chapter:
            metadata['chapter'] = chapter
            metadata['extraction_method'] = 'chapter_header'
            metadata['confidence'] += 0.4
        
        # Strategy 2: Look for hadith numbers
        hadith = self._extract_hadith_advanced(clean_text)
        if hadith:
            metadata['hadith_number'] = hadith
            metadata['extraction_method'] = 'hadith_number' if not metadata['extraction_method'] else 'both'
            metadata['confidence'] += 0.4
        
        # Strategy 3: Context-based extraction
        context_data = self._extract_from_context(clean_text)
        if context_data['chapter'] and not metadata['chapter']:
            metadata['chapter'] = context_data['chapter']
            metadata['extraction_method'] = 'context'
            metadata['confidence'] += 0.2
            
        if context_data['hadith'] and not metadata['hadith_number']:
            metadata['hadith_number'] = context_data['hadith']
            metadata['extraction_method'] = 'context' if not metadata['extraction_method'] else metadata['extraction_method'] + '_context'
            metadata['confidence'] += 0.2
        
        return metadata
    
    def _clean_text_for_extraction(self, text: str) -> str:
        """Clean text and prepare for metadata extraction"""
        # Remove URLs and common headers
        text = re.sub(r'www\.hubeali\.com', '', text, flags=re.IGNORECASE)
        text = re.sub(r'bihar\s+al-anwaar\s+volume\s+\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
        
        # Clean extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _extract_chapter_advanced(self, text: str) -> Optional[str]:
        """Advanced chapter extraction with multiple patterns"""
        
        # First 500 characters are most likely to contain chapter info
        text_sample = text[:500].lower()
        
        for pattern in self.chapter_patterns:
            matches = re.finditer(pattern, text_sample, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                chapter_num = match.group(1)
                
                # Validate chapter number (should be reasonable)
                if chapter_num.isdigit() and 1 <= int(chapter_num) <= 200:
                    # Check if it's not in exclusion context
                    context = text_sample[max(0, match.start()-20):match.end()+20]
                    if not any(re.search(excl, context, re.IGNORECASE) for excl in self.exclusion_patterns):
                        return chapter_num
        
        return None
    
    def _extract_hadith_advanced(self, text: str) -> Optional[str]:
        """Advanced hadith extraction with context validation"""
        
        # Look in first 300 characters for hadith numbers
        text_sample = text[:300].lower()
        
        for pattern in self.hadith_patterns:
            matches = re.finditer(pattern, text_sample, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                hadith_num = match.group(1)
                
                # Validate hadith number
                if hadith_num.isdigit() and 1 <= int(hadith_num) <= 10000:
                    # Check context for validation
                    context = text_sample[max(0, match.start()-30):match.end()+30]
                    
                    # Should not be page numbers or other numbers
                    invalid_contexts = ['page', 'volume', 'year', 'صفحة', 'مجلد']
                    if not any(invalid in context for invalid in invalid_contexts):
                        return hadith_num
        
        return None
    
    def _extract_from_context(self, text: str) -> Dict:
        """Extract metadata from surrounding context"""
        
        result = {'chapter': None, 'hadith': None}
        
        # Look for table of contents patterns
        if 'table of contents' in text.lower() or 'فهرست' in text:
            # Try to extract from TOC format
            toc_chapter = self._extract_from_toc(text)
            if toc_chapter:
                result['chapter'] = toc_chapter
        
        # Look for sequential patterns
        lines = text.split('\n')
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            # Pattern: Number followed by content that looks like hadith
            if re.match(r'^\s*\d+\s*[-–—.]\s*', line):
                number_match = re.match(r'^\s*(\d+)', line)
                if number_match:
                    num = number_match.group(1)
                    
                    # Check if next lines contain hadith-like content
                    following_text = ' '.join(lines[i:i+3]).lower()
                    hadith_indicators = ['said', 'narrated', 'reported', 'قال', 'عن', 'حدثنا']
                    
                    if any(indicator in following_text for indicator in hadith_indicators):
                        if not result['hadith'] and 1 <= int(num) <= 1000:
                            result['hadith'] = num
        
        return result
    
    def _extract_from_toc(self, text: str) -> Optional[str]:
        """Extract chapter from table of contents"""
        
        lines = text.split('\n')
        for line in lines:
            # TOC pattern: "CHAPTER 1 – TITLE"
            toc_match = re.search(r'chapter\s+(\d+)\s*[-–—]', line, re.IGNORECASE)
            if toc_match:
                return toc_match.group(1)
        
        return None

def analyze_current_metadata():
    """Analyze what metadata currently exists"""
    print("🔍 ANALYZING CURRENT METADATA")
    print("=" * 50)
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get overall statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_chunks,
                COUNT(CASE WHEN chapter_name IS NOT NULL THEN 1 END) as with_chapter,
                COUNT(CASE WHEN hadith_number IS NOT NULL THEN 1 END) as with_hadith,
                COUNT(DISTINCT volume_number) as total_volumes
            FROM bihar_chunks
        """)
        
        stats = cursor.fetchone()
        print(f"📊 Overall Statistics:")
        print(f"   Total chunks: {stats['total_chunks']}")
        print(f"   With chapter: {stats['with_chapter']} ({stats['with_chapter']/stats['total_chunks']*100:.1f}%)")
        print(f"   With hadith: {stats['with_hadith']} ({stats['with_hadith']/stats['total_chunks']*100:.1f}%)")
        print(f"   Total volumes: {stats['total_volumes']}")
        
        # Volume-wise breakdown
        cursor.execute("""
            SELECT 
                volume_number,
                COUNT(*) as total_chunks,
                COUNT(CASE WHEN chapter_name IS NOT NULL THEN 1 END) as with_chapter,
                COUNT(CASE WHEN hadith_number IS NOT NULL THEN 1 END) as with_hadith
            FROM bihar_chunks
            GROUP BY volume_number
            ORDER BY volume_number
        """)
        
        volumes = cursor.fetchall()
        print(f"\n📚 Volume-wise Breakdown:")
        print("Vol | Chunks | Chapter | Hadith")
        print("-" * 35)
        
        for vol in volumes:
            chapter_pct = vol['with_chapter']/vol['total_chunks']*100 if vol['total_chunks'] > 0 else 0
            hadith_pct = vol['with_hadith']/vol['total_chunks']*100 if vol['total_chunks'] > 0 else 0
            print(f"{vol['volume_number']:3d} | {vol['total_chunks']:6d} | {chapter_pct:5.1f}% | {hadith_pct:5.1f}%")
        
        # Sample problematic chunks
        cursor.execute("""
            SELECT id, volume_number, LEFT(full_text, 200) as text_sample
            FROM bihar_chunks 
            WHERE chapter_name IS NULL AND hadith_number IS NULL
            AND LENGTH(full_text) > 100
            ORDER BY volume_number, id
            LIMIT 5
        """)
        
        samples = cursor.fetchall()
        print(f"\n🔍 Sample chunks with missing metadata:")
        for i, chunk in enumerate(samples, 1):
            print(f"\n{i}. Volume {chunk['volume_number']}, ID {chunk['id']}:")
            print(f"   Text: {chunk['text_sample']}...")
        
        return stats, volumes
        
    except Exception as e:
        print(f"❌ Error analyzing metadata: {e}")
        return None, None
    finally:
        cursor.close()

def fix_metadata_for_volumes(volume_list: List[int] = [1, 3, 7], limit_per_volume: int = 500):
    """Fix metadata for specific volumes"""
    
    print(f"\n🔧 FIXING METADATA FOR VOLUMES: {volume_list}")
    print("=" * 50)
    
    extractor = MetadataExtractor()
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    total_fixed = 0
    
    for volume in volume_list:
        print(f"\n📖 Processing Volume {volume}...")
        
        try:
            # Get chunks with missing metadata
            cursor.execute("""
                SELECT id, volume_number, full_text, chapter_name, hadith_number
                FROM bihar_chunks 
                WHERE volume_number = %s 
                AND (chapter_name IS NULL OR hadith_number IS NULL)
                AND LENGTH(full_text) > 50
                ORDER BY chunk_index
                LIMIT %s
            """, [volume, limit_per_volume])
            
            chunks = cursor.fetchall()
            print(f"   Found {len(chunks)} chunks to process")
            
            volume_fixed = 0
            
            for i, chunk in enumerate(chunks):
                if i % 50 == 0:  # Progress update
                    print(f"   Progress: {i}/{len(chunks)}")
                
                # Extract metadata
                extracted = extractor.extract_metadata_advanced(
                    chunk['full_text'], 
                    chunk['volume_number']
                )
                
                # Only update if we found something and confidence is reasonable
                if extracted['confidence'] > 0.2:
                    update_needed = False
                    new_chapter = chunk['chapter_name']
                    new_hadith = chunk['hadith_number']
                    
                    if not chunk['chapter_name'] and extracted['chapter']:
                        new_chapter = extracted['chapter']
                        update_needed = True
                    
                    if not chunk['hadith_number'] and extracted['hadith_number']:
                        new_hadith = extracted['hadith_number']
                        update_needed = True
                    
                    if update_needed:
                        # Update the database
                        cursor.execute("""
                            UPDATE bihar_chunks 
                            SET 
                                chapter_name = %s,
                                hadith_number = %s,
                                metadata = metadata || %s
                            WHERE id = %s
                        """, (
                            new_chapter,
                            new_hadith,
                            Json({
                                'chapter': extracted['chapter'],
                                'hadith_number': extracted['hadith_number'],
                                'extraction_method': extracted['extraction_method'],
                                'confidence': extracted['confidence'],
                                'fixed_metadata': True
                            }),
                            chunk['id']
                        ))
                        
                        volume_fixed += 1
                        total_fixed += 1
            
            # Commit changes for this volume
            conn.commit()
            print(f"   ✅ Fixed {volume_fixed} chunks in Volume {volume}")
            
        except Exception as e:
            conn.rollback()
            print(f"   ❌ Error processing Volume {volume}: {e}")
    
    cursor.close()
    print(f"\n🎉 TOTAL FIXED: {total_fixed} chunks across {len(volume_list)} volumes")
    
    return total_fixed

def validate_fixes():
    """Validate the metadata fixes"""
    print(f"\n✅ VALIDATING METADATA FIXES")
    print("=" * 50)
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Check improvement statistics
        cursor.execute("""
            SELECT 
                volume_number,
                COUNT(*) as total_chunks,
                COUNT(CASE WHEN chapter_name IS NOT NULL THEN 1 END) as with_chapter,
                COUNT(CASE WHEN hadith_number IS NOT NULL THEN 1 END) as with_hadith,
                COUNT(CASE WHEN metadata->>'fixed_metadata' = 'true' THEN 1 END) as fixed_chunks
            FROM bihar_chunks
            WHERE volume_number IN (1, 3, 7)
            GROUP BY volume_number
            ORDER BY volume_number
        """)
        
        results = cursor.fetchall()
        
        print("Vol | Total | Chapter | Hadith | Fixed")
        print("-" * 40)
        
        for vol in results:
            chapter_pct = vol['with_chapter']/vol['total_chunks']*100
            hadith_pct = vol['with_hadith']/vol['total_chunks']*100
            
            print(f"{vol['volume_number']:3d} | {vol['total_chunks']:5d} | {chapter_pct:5.1f}% | {hadith_pct:5.1f}% | {vol['fixed_chunks']:5d}")
        
        # Show some examples of fixed metadata
        cursor.execute("""
            SELECT volume_number, chapter_name, hadith_number, 
                   metadata->>'extraction_method' as method,
                   LEFT(full_text, 150) as text_sample
            FROM bihar_chunks 
            WHERE metadata->>'fixed_metadata' = 'true'
            AND chapter_name IS NOT NULL
            ORDER BY volume_number, chapter_name::int
            LIMIT 10
        """)
        
        examples = cursor.fetchall()
        print(f"\n🔍 Examples of fixed metadata:")
        
        for ex in examples[:5]:
            print(f"\nVolume {ex['volume_number']}, Chapter {ex['chapter_name']}, Hadith {ex['hadith_number']}")
            print(f"Method: {ex['method']}")
            print(f"Text: {ex['text_sample']}...")
        
    except Exception as e:
        print(f"❌ Error validating fixes: {e}")
    finally:
        cursor.close()

def main():
    """Main execution function"""
    print("🔧 BIHAR UL ANWAR METADATA FIXER")
    print("=" * 60)
    
    # Step 1: Analyze current state
    analyze_current_metadata()
    
    # Step 2: Fix metadata for priority volumes
    total_fixed = fix_metadata_for_volumes([1, 3, 7], limit_per_volume=500)
    
    # Step 3: Validate fixes
    if total_fixed > 0:
        validate_fixes()
    
    print(f"\n🎯 NEXT STEPS:")
    print("1. Test reference search with fixed metadata")
    print("2. Test query quality with better references")
    print("3. Proceed to Phase 1.2 (System Prompts)")
    
    print(f"\n💡 RUN TESTS:")
    print("curl 'http://localhost:8000/search-by-reference?volume=1&chapter=1'")
    print("curl 'http://localhost:8000/search-by-reference?volume=3&chapter=1'")

if __name__ == "__main__":
    main()