# fixes.py - Complete diagnostic and testing script
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your modules
from database import get_db_connection
from processing import generate_query_embedding
import google.generativeai as genai
from config import EMBEDDING_MODEL

def test_embedding_generation():
    """Test if embedding generation is working"""
    print("🧪 Testing Embedding Generation")
    print("=" * 40)
    
    test_queries = [
        "resurrection",
        "judgment day", 
        "scale mizan"
    ]
    
    for query in test_queries:
        try:
            embedding = generate_query_embedding(query)
            is_valid = len(embedding) == 768 and not all(x == 0.0 for x in embedding)
            status = "✅ Valid" if is_valid else "❌ Invalid"
            print(f"Query: '{query}' → {status} (dim: {len(embedding)})")
            
        except Exception as e:
            print(f"Query: '{query}' → ❌ Error: {e}")

def check_database_embeddings():
    """Check if database has valid embeddings"""
    print("\n🔍 Checking Database Embeddings")
    print("=" * 40)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check total chunks
        cursor.execute("SELECT COUNT(*) FROM bihar_chunks")
        total_chunks = cursor.fetchone()[0]
        
        # Check chunks with embeddings
        cursor.execute("SELECT COUNT(*) FROM bihar_chunks WHERE embedding IS NOT NULL")
        chunks_with_embeddings = cursor.fetchone()[0]
        
        # Check Volume 7 specifically
        cursor.execute("SELECT COUNT(*) FROM bihar_chunks WHERE volume_number = 7 AND embedding IS NOT NULL")
        vol7_with_embeddings = cursor.fetchone()[0]
        
        print(f"📊 Total chunks: {total_chunks}")
        print(f"📊 Chunks with embeddings: {chunks_with_embeddings}")
        print(f"📖 Volume 7 with embeddings: {vol7_with_embeddings}")
        
        # Check a sample embedding
        cursor.execute("SELECT embedding FROM bihar_chunks WHERE volume_number = 7 AND embedding IS NOT NULL LIMIT 1")
        sample = cursor.fetchone()
        
        if sample and sample[0]:
            embedding_dim = len(sample[0])
            is_zero = all(x == 0.0 for x in sample[0][:10])  # Check first 10 dimensions
            print(f"📋 Sample embedding: dim={embedding_dim}, is_zero={is_zero}")
        else:
            print("❌ No valid embeddings found")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Database check error: {e}")

def test_direct_embedding_api():
    """Test Gemini embedding API directly"""
    print("\n🧪 Testing Direct Gemini API")
    print("=" * 40)
    
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content="test query",
            task_type="RETRIEVAL_QUERY"
        )
        
        if 'embedding' in result:
            print(f"✅ Direct API works: {len(result['embedding'])} dimensions")
        else:
            print(f"❌ API response missing embedding: {result}")
            
    except Exception as e:
        print(f"❌ Direct API error: {e}")

def main():
    """Run all diagnostics"""
    print("🔧 RUNNING CRITICAL DIAGNOSTICS")
    print("=" * 50)
    
    # Test direct API first
    test_direct_embedding_api()
    
    # Test embedding generation through our function
    test_embedding_generation()
    
    # Check database embeddings
    check_database_embeddings()
    
    print("\n💡 NEXT STEPS:")
    print("1. If embedding generation fails → Fix processing.py")
    print("2. If database has no embeddings → Reprocess volumes")
    print("3. If embeddings are all zeros → Check API key/model")
    print("4. Apply fixes to database.py and processing.py")
    print("5. Restart server and test again")

if __name__ == "__main__":
    main()