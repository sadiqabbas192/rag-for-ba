# processing.py - Complete processing with enhanced functions
import time
import re
import gc
import os
from typing import List, Dict
from pathlib import Path
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from config import EMBEDDING_MODEL, CHAT_MODEL, CHUNK_SIZE, CHUNK_OVERLAP

# OPTIMIZED LIMITS FOR BETTER PERFORMANCE
MAX_PAGES_PER_VOLUME = 100  # Reduced from 200
EMBEDDING_BATCH_SIZE = 2    # Reduced from 3
PROCESSING_DELAY = 0.5      # Increased delay between API calls

# ENHANCED SYSTEM PROMPT FOR BIHAR UL ANWAR
ENHANCED_SYSTEM_PROMPT = """You are a specialist in Bihar ul Anwar, the 110-volume hadith collection by Allama Muhammad Baqir Majlisi. You MUST follow these strict rules:

CONTENT RULES:
1. Use ONLY the provided excerpts from Bihar ul Anwar - NO external knowledge
2. If the excerpts don't contain enough information, say "The provided excerpts are insufficient"
3. NEVER add general Islamic knowledge not found in the excerpts
4. Focus ONLY on actual hadith/traditions, NOT table of contents or indexes

REFERENCE RULES:
1. ALWAYS cite sources as: "Bihar ul Anwar, Volume X, Chapter Y, Hadith Z"
2. If hadith number is missing, use: "Bihar ul Anwar, Volume X, Chapter Y"
3. If chapter is missing, use: "Bihar ul Anwar, Volume X"
4. NEVER include long quotes - only give clean references

RESPONSE FORMAT:
1. Start with a direct answer based ONLY on provided content
2. List specific references at the end
3. If asking about a chapter summary, extract ONLY key points from that chapter
4. Do NOT elaborate beyond what's in the excerpts

FORBIDDEN:
- General Islamic explanations not in the text
- Interpretations beyond the provided content  
- Long quotations in responses
- References to sources other than Bihar ul Anwar
- Table of contents or index information as hadith content"""

def extract_hadith_metadata(text: str, volume_num: int) -> Dict:
    """Extract hadith metadata from text - OPTIMIZED"""
    metadata = {
        'volume': volume_num,
        'chapter': None,
        'hadith_number': None
    }
    
    # Only check first 500 characters for metadata
    text_sample = text[:500].lower()
    
    # Chapter patterns
    chapter_patterns = [
        r'chapter\s+(\d+)',
        r'bab\s+(\d+)', 
        r'باب\s+(\d+)',
        r'ch(?:apter)?\.?\s*(\d+)'
    ]
    
    for pattern in chapter_patterns:
        match = re.search(pattern, text_sample)
        if match:
            metadata['chapter'] = match.group(1)
            break
    
    # Hadith patterns
    hadith_patterns = [
        r'hadith\s+#?(\d+)',
        r'tradition\s+#?(\d+)',
        r'h\.?\s*(\d+)',
        r'حديث\s+(\d+)'
    ]
    
    for pattern in hadith_patterns:
        match = re.search(pattern, text_sample)
        if match:
            metadata['hadith_number'] = match.group(1)
            break
    
    return metadata

def split_arabic_english(text: str) -> tuple:
    """Separate Arabic and English text - OPTIMIZED"""
    if not text or len(text) < 10:
        return "", text
    
    arabic_text = ""
    english_text = ""
    
    lines = text.split('\n')
    # Process max 50 lines to save time
    for line in lines[:50]:
        line = line.strip()
        if not line or len(line) < 3:
            continue
            
        # Count Arabic characters
        arabic_count = sum(1 for char in line if '\u0600' <= char <= '\u06FF')
        total_chars = len([c for c in line if c.isalpha()])
        
        if total_chars > 0 and arabic_count / total_chars > 0.3:  # 30% threshold
            arabic_text += line + "\n"
        else:
            english_text += line + "\n"
    
    # Limit length to prevent excessive text
    return arabic_text.strip()[:1000], english_text.strip()[:1000]

def process_pdf_text(pdf_path: str, volume_num: int, max_pages: int = MAX_PAGES_PER_VOLUME) -> List[Dict]:
    """Process PDF and extract text chunks - OPTIMIZED"""
    try:
        print(f"📖 Processing PDF: {Path(pdf_path).name}")
        
        # Check file size first
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        print(f"📊 File size: {file_size_mb:.1f} MB")
        
        # Adjust max pages based on file size
        if file_size_mb > 8:  # Large files
            max_pages = min(max_pages, 50)
            print(f"⚠️ Large file detected, limiting to {max_pages} pages")
        
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        pages_to_process = min(total_pages, max_pages)
        
        print(f"📄 Processing {pages_to_process}/{total_pages} pages")
        
        # Optimized text splitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "۔", "।"],
            length_function=len
        )
        
        all_chunks = []
        
        # Process in smaller batches to reduce memory usage
        batch_size = 3  # Process 3 pages at a time
        
        for batch_start in range(0, pages_to_process, batch_size):
            batch_end = min(batch_start + batch_size, pages_to_process)
            print(f"  📝 Processing pages {batch_start + 1}-{batch_end}")
            
            # Extract text from current batch
            batch_text = ""
            for page_num in range(batch_start, batch_end):
                try:
                    text = reader.pages[page_num].extract_text()
                    if text and text.strip():
                        # Clean the text
                        cleaned_text = text.replace('\x00', '').strip()
                        if len(cleaned_text) > 50:  # Only add substantial text
                            batch_text += f"\n--- Page {page_num + 1} ---\n" + cleaned_text
                except Exception as e:
                    print(f"    ⚠️ Error on page {page_num + 1}: {e}")
                    continue
            
            if not batch_text.strip():
                print(f"    ⚠️ No text extracted from pages {batch_start + 1}-{batch_end}")
                continue
            
            # Split into chunks
            try:
                chunks = splitter.split_text(batch_text)
                print(f"    ✅ Created {len(chunks)} chunks from pages {batch_start + 1}-{batch_end}")
                
                for chunk_idx, chunk in enumerate(chunks):
                    if len(chunk.strip()) < 50:  # Skip tiny chunks
                        continue
                    
                    # Separate Arabic and English
                    arabic, english = split_arabic_english(chunk)
                    
                    # Extract metadata
                    metadata = extract_hadith_metadata(chunk, volume_num)
                    metadata['pages_processed'] = f"{batch_start + 1}-{batch_end}"
                    metadata['total_pages'] = total_pages
                    metadata['file_size_mb'] = round(file_size_mb, 1)
                    
                    chunk_data = {
                        'volume_number': volume_num,
                        'arabic_text': arabic,
                        'english_text': english,
                        'full_text': chunk,
                        'chunk_index': len(all_chunks),
                        'metadata': metadata
                    }
                    
                    all_chunks.append(chunk_data)
                
            except Exception as e:
                print(f"    ❌ Error processing batch {batch_start + 1}-{batch_end}: {e}")
                continue
            
            # Memory cleanup after each batch
            del batch_text, chunks
            gc.collect()
        
        print(f"✅ Total chunks created: {len(all_chunks)} from {pages_to_process} pages")
        return all_chunks
        
    except Exception as e:
        print(f"❌ PDF processing error: {str(e)}")
        raise Exception(f"Error processing PDF: {str(e)}")

def generate_embeddings(texts: List[str], batch_size: int = EMBEDDING_BATCH_SIZE) -> List[List[float]]:
    """Generate embeddings for text chunks - OPTIMIZED"""
    embeddings = []
    total_texts = len(texts)
    
    print(f"🔄 Generating embeddings for {total_texts} texts (batch size: {batch_size})")
    
    for i in range(0, total_texts, batch_size):
        batch = texts[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total_texts + batch_size - 1) // batch_size
        
        print(f"  ⚡ Processing embedding batch {batch_num}/{total_batches}")
        
        for j, text in enumerate(batch):
            try:
                # Limit text length more aggressively
                limited_text = text[:4000] if len(text) > 4000 else text
                
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=limited_text,
                    task_type="RETRIEVAL_DOCUMENT"
                )
                
                if 'embedding' in result and result['embedding']:
                    embeddings.append(result['embedding'])
                else:
                    print(f"    ⚠️ Empty embedding for text {i + j + 1}")
                    embeddings.append([0.0] * 768)
                
                # Longer delay to avoid rate limits
                time.sleep(PROCESSING_DELAY)
                
            except Exception as e:
                print(f"    ❌ Embedding error for text {i + j + 1}: {str(e)}")
                embeddings.append([0.0] * 768)
                time.sleep(1)  # Wait longer on error
        
        # Additional delay between batches
        if batch_num < total_batches:
            time.sleep(2)
    
    valid_embeddings = sum(1 for emb in embeddings if not all(x == 0.0 for x in emb))
    print(f"✅ Generated {valid_embeddings}/{len(embeddings)} valid embeddings")
    
    return embeddings

def generate_query_embedding(query: str) -> List[float]:
    """Generate embedding for search query - FIXED VERSION"""
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=query,
            task_type="RETRIEVAL_QUERY"
        )
        
        if 'embedding' in result:
            return result['embedding']
        else:
            print(f"❌ No embedding in result: {result}")
            return [0.0] * 768
            
    except Exception as e:
        print(f"❌ Embedding generation error: {e}")
        # Return zero embedding as fallback
        return [0.0] * 768

def filter_relevant_chunks(chunks: List[Dict], query: str) -> List[Dict]:
    """FIXED: Filter out irrelevant chunks but keep actual content"""
    
    filtered_chunks = []
    
    # Much more restrictive exclude patterns - only exclude obvious non-content
    exclude_patterns = [
        r'^table of contents$',           # Only pure TOC lines
        r'^overall.*index$',              # Only pure index lines  
        r'^bihar al-anwaar\s+volume \d+$', # Only pure headers
    ]
    
    # Keep hadith indicators
    include_patterns = [
        r'said.*asws',
        r'narrated',
        r'reported', 
        r'tradition',
        r'hadith',
        r'قال',
        r'عن',
        r'حدثنا',
        r'روى',
        r'chapter \d+',                   # Chapter headers are content
        r'knowledge',                     # For knowledge-related queries
        r'علم',                           # Arabic for knowledge
    ]
    
    for chunk in chunks:
        full_text = chunk.get('full_text', '').lower().strip()
        english_text = chunk.get('english_text', '').lower()
        
        # Only exclude if it's PURELY navigation (very restrictive)
        should_exclude = False
        for pattern in exclude_patterns:
            if re.match(pattern, full_text):  # Only exact matches
                should_exclude = True
                break
        
        # If text is very short and has no content indicators, exclude
        if len(full_text) < 50 and not any(re.search(p, full_text) for p in include_patterns):
            should_exclude = True
        
        if not should_exclude:
            # Check for hadith content
            has_hadith_content = any(re.search(pattern, english_text) for pattern in include_patterns)
            
            # Check query relevance
            is_relevant = _is_relevant_to_query(chunk, query)
            
            if has_hadith_content or is_relevant:
                chunk['relevance_score'] = 1.0 if has_hadith_content else 0.7
                filtered_chunks.append(chunk)
    
    # Sort by relevance and similarity
    filtered_chunks.sort(key=lambda x: (
        x.get('relevance_score', 0),
        x.get('similarity', 0)
    ), reverse=True)
    
    # Return more chunks to give AI more content to work with
    return filtered_chunks[:7]  # Increased from 5 to 7


def _is_relevant_to_query(chunk: Dict, query: str) -> bool:
    """IMPROVED: More permissive relevance checking"""
    
    query_lower = query.lower()
    full_text = chunk.get('full_text', '').lower()
    english_text = chunk.get('english_text', '').lower()
    
    # For chapter-specific queries
    if 'chapter' in query_lower:
        chapter_match = re.search(r'chapter\s+(\d+)', query_lower)
        if chapter_match:
            requested_chapter = chapter_match.group(1)
            chunk_chapter = chunk.get('chapter_name')
            
            # Accept if chapter matches
            if chunk_chapter == requested_chapter:
                return True
            
            # Accept if chapter is mentioned in text
            if f'chapter {requested_chapter}' in full_text:
                return True
    
    # For knowledge-related queries (more specific)
    if 'knowledge' in query_lower:
        knowledge_terms = ['knowledge', 'learn', 'scholar', 'علم', 'طلب', 'عالم']
        if any(term in full_text or term in english_text for term in knowledge_terms):
            return True
    
    # For general concept queries, use term overlap
    query_terms = re.findall(r'\b\w{3,}\b', query_lower)  # Only words 3+ chars
    text_words = set(re.findall(r'\b\w{3,}\b', full_text))
    
    if query_terms:
        overlap = len(set(query_terms) & text_words)
        overlap_ratio = overlap / len(query_terms)
        return overlap_ratio > 0.15  # Lowered from 0.2 to 0.15
    
    return True  # Default to include if no specific exclusion

def _post_process_response(answer: str, references: List[str]) -> str:
    """Clean up and validate the AI response"""
    
    # Remove common AI disclaimers
    disclaimer_patterns = [
        r'as an ai.*?,',
        r'based on my knowledge.*?,',
        r'in islamic tradition.*?,',
        r'generally speaking.*?,',
    ]
    
    for pattern in disclaimer_patterns:
        answer = re.sub(pattern, '', answer, flags=re.IGNORECASE)
    
    # Ensure response starts directly with content
    answer = answer.strip()
    
    # Validate that references are properly formatted
    clean_refs = []
    for ref in references[:3]:  # Max 3 references
        if 'Bihar ul Anwar' in ref:
            clean_refs.append(ref)
    
    # Add clean reference section if not already present
    if clean_refs and 'References:' not in answer:
        answer += f"\n\nReferences:\n"
        for ref in clean_refs:
            answer += f"- {ref}\n"
    
    return answer

def generate_answer_with_context(query: str, chunks: List[Dict], include_arabic: bool = True) -> str:
    """ENHANCED: Generate answer with enhanced prompting and filtering"""
    
    # Filter chunks first
    filtered_chunks = filter_relevant_chunks(chunks, query)
    
    if not filtered_chunks:
        return "The provided excerpts from Bihar ul Anwar do not contain sufficient information to answer your question about the requested content."
    
    # Prepare context with better formatting
    context_parts = []
    reference_list = []
    
    for i, chunk in enumerate(filtered_chunks, 1):
        volume = chunk.get('volume_number', 'Unknown')
        metadata = chunk.get('metadata', {})
        chapter = metadata.get('chapter', 'Unknown')
        hadith_num = metadata.get('hadith_number', 'Unknown')
        
        # Build reference
        ref = f"Bihar ul Anwar, Volume {volume}"
        if chapter and chapter != 'Unknown':
            ref += f", Chapter {chapter}"
        if hadith_num and hadith_num != 'Unknown':
            ref += f", Hadith {hadith_num}"
        
        reference_list.append(ref)
        
        # Prepare context (shorter excerpts)
        context_part = f"\n[Excerpt {i}] {ref}\n"
        
        if include_arabic and chunk.get('arabic_text'):
            arabic_excerpt = chunk['arabic_text'][:300]  # Shorter excerpts
            context_part += f"Arabic: {arabic_excerpt}\n"
        
        if chunk.get('english_text'):
            english_excerpt = chunk['english_text'][:300]  # Shorter excerpts
            context_part += f"English: {english_excerpt}\n"
        
        context_parts.append(context_part)
    
    context = "\n".join(context_parts)
    
    # Create enhanced prompt
    prompt = f"""{ENHANCED_SYSTEM_PROMPT}

EXCERPTS FROM BIHAR UL ANWAR:
{context}

USER QUESTION: {query}

INSTRUCTIONS: Answer using ONLY the content above. Provide specific Bihar ul Anwar references. Do NOT add external knowledge or long quotes.

ANSWER:"""
    
    # Generate response with strict settings
    try:
        generation_config = genai.types.GenerationConfig(
            temperature=0.3,  # Lower temperature for more focused responses
            max_output_tokens=1500,  # Shorter responses
            candidate_count=1,
        )
        
        response = CHAT_MODEL.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        # Post-process response
        answer = response.text
        answer = _post_process_response(answer, reference_list)
        
        return answer
        
    except Exception as e:
        print(f"❌ Enhanced answer generation error: {e}")
        return f"I apologize, but I encountered an error while processing the Bihar ul Anwar excerpts. Please try rephrasing your question."