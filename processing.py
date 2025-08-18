# processing.py - PDF Processing and Embeddings
import time
import re
from typing import List, Dict
from pathlib import Path
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from config import EMBEDDING_MODEL, CHAT_MODEL, SYSTEM_PROMPT, MAX_PAGES_PER_VOLUME, CHUNK_SIZE, CHUNK_OVERLAP

def extract_hadith_metadata(text: str, volume_num: int) -> Dict:
    """Extract hadith metadata from text"""
    metadata = {
        'volume': volume_num,
        'chapter': None,
        'hadith_number': None
    }
    
    text_lower = text.lower()
    
    # Chapter patterns
    chapter_patterns = [
        r'chapter\s+(\d+)',
        r'bab\s+(\d+)',
        r'باب\s+(\d+)',
        r'ch(?:apter)?\.?\s*(\d+)'
    ]
    
    for pattern in chapter_patterns:
        match = re.search(pattern, text_lower)
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
        match = re.search(pattern, text_lower)
        if match:
            metadata['hadith_number'] = match.group(1)
            break
    
    return metadata

def split_arabic_english(text: str) -> tuple:
    """Separate Arabic and English text"""
    arabic_text = ""
    english_text = ""
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Count Arabic characters
        arabic_count = sum(1 for char in line if '\u0600' <= char <= '\u06FF')
        total_chars = len([c for c in line if c.isalpha()])
        
        if total_chars > 0 and arabic_count / total_chars > 0.3:  # 30% threshold
            arabic_text += line + "\n"
        else:
            english_text += line + "\n"
    
    return arabic_text.strip(), english_text.strip()

def process_pdf_text(pdf_path: str, volume_num: int, max_pages: int = MAX_PAGES_PER_VOLUME) -> List[Dict]:
    """Process PDF and extract text chunks"""
    try:
        print(f"Processing PDF: {Path(pdf_path).name}")
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        
        # Limit pages for large files
        if total_pages > max_pages:
            print(f"Large file detected ({total_pages} pages), processing first {max_pages} pages")
            pages_to_process = max_pages
        else:
            pages_to_process = total_pages
        
        # Text splitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "۔", "।"],
            length_function=len
        )
        
        all_chunks = []
        
        # Process pages in batches
        batch_size = 5
        for batch_start in range(0, pages_to_process, batch_size):
            batch_end = min(batch_start + batch_size, pages_to_process)
            
            # Extract text from batch
            batch_text = ""
            for page_num in range(batch_start, batch_end):
                try:
                    text = reader.pages[page_num].extract_text()
                    if text and text.strip():
                        batch_text += f"\n--- Page {page_num + 1} ---\n" + text
                except Exception as e:
                    print(f"Error on page {page_num + 1}: {e}")
                    continue
            
            if not batch_text.strip():
                continue
            
            # Split into chunks
            chunks = splitter.split_text(batch_text)
            
            for chunk_idx, chunk in enumerate(chunks):
                if len(chunk.strip()) < 50:  # Skip very small chunks
                    continue
                
                # Separate Arabic and English
                arabic, english = split_arabic_english(chunk)
                
                # Extract metadata
                metadata = extract_hadith_metadata(chunk, volume_num)
                metadata['pages_processed'] = f"{batch_start + 1}-{batch_end}"
                metadata['total_pages'] = total_pages
                
                chunk_data = {
                    'volume_number': volume_num,
                    'arabic_text': arabic,
                    'english_text': english,
                    'full_text': chunk,
                    'chunk_index': len(all_chunks),
                    'metadata': metadata
                }
                
                all_chunks.append(chunk_data)
        
        print(f"Created {len(all_chunks)} chunks from {pages_to_process} pages")
        return all_chunks
        
    except Exception as e:
        print(f"PDF processing error: {str(e)}")
        raise Exception(f"Error processing PDF: {str(e)}")

def generate_embeddings(texts: List[str], batch_size: int = 3) -> List[List[float]]:
    """Generate embeddings for text chunks"""
    embeddings = []
    total_texts = len(texts)
    
    print(f"Generating embeddings for {total_texts} texts in batches of {batch_size}")
    
    for i in range(0, total_texts, batch_size):
        batch = texts[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total_texts + batch_size - 1) // batch_size
        
        print(f"  Processing embedding batch {batch_num}/{total_batches}")
        
        for text in batch:
            try:
                # Limit text length to prevent API errors
                limited_text = text[:8000] if len(text) > 8000 else text
                
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=limited_text,
                    task_type="RETRIEVAL_DOCUMENT"
                )
                embeddings.append(result['embedding'])
                
                # Rate limiting
                time.sleep(0.2)
                
            except Exception as e:
                print(f"Embedding error: {str(e)}")
                # Add zero embedding for failed text
                embeddings.append([0.0] * 768)
    
    print(f"Generated {len(embeddings)} embeddings")
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
    
    # Create prompt
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