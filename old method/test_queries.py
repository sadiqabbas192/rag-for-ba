# test_queries.py - Test queries for Bihar ul Anwar RAG system

import requests
import json
import time

API_URL = "http://localhost:8000"

# Sample queries related to Bihar ul Anwar topics
TEST_QUERIES = [
    {
        "query": "What are the traditions about the creation of Prophet Muhammad (PBUH) and his noor (light)?",
        "description": "Testing creation narratives"
    },
    {
        "query": "Find hadiths about the creation of Imam Ali (AS) and Ahlul Bayt",
        "description": "Testing Ahlul Bayt references"
    },
    {
        "query": "What does Bihar ul Anwar say about the event of Ghadir Khumm?",
        "description": "Testing historical events"
    },
    {
        "query": "Find traditions about the twelve Imams and their names",
        "description": "Testing Imams references"
    },
    {
        "query": "What are the signs of appearance of Imam Mahdi according to Bihar ul Anwar?",
        "description": "Testing eschatological content"
    },
    {
        "query": "Find hadiths about the martyrdom of Imam Hussain in Karbala",
        "description": "Testing Karbala narratives"
    },
    {
        "query": "What virtues of Fatima Zahra are mentioned in Bihar ul Anwar?",
        "description": "Testing content about Fatima (SA)"
    },
    {
        "query": "Find traditions about the knowledge and miracles of the Imams",
        "description": "Testing miraculous narratives"
    }
]

def test_single_query(query_data):
    """Test a single query"""
    print(f"\n{'='*60}")
    print(f"📖 Testing: {query_data['description']}")
    print(f"❓ Query: {query_data['query'][:100]}...")
    print("-" * 40)
    
    payload = {
        "query": query_data["query"],
        "top_k": 5,
        "include_arabic": True
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{API_URL}/query", json=payload, timeout=30)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Success in {elapsed:.2f} seconds")
            print(f"📚 Found {data['total_sources']} relevant sources")
            
            # Show answer preview
            answer = data['answer'][:300] + "..." if len(data['answer']) > 300 else data['answer']
            print(f"\n💬 Answer Preview:\n{answer}")
            
            # Show references
            if data['references']:
                print(f"\n📚 Top References:")
                for i, ref in enumerate(data['references'][:3], 1):
                    print(f"   {i}. Volume {ref['volume']}, Chapter {ref['chapter']}, Hadith {ref['hadith_number']}")
                    print(f"      Similarity: {ref['similarity_score']}")
            
            return True
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_reference_search():
    """Test searching by specific reference"""
    print(f"\n{'='*60}")
    print("🔍 Testing Reference Search")
    print("-" * 40)
    
    # Test searching for specific volume
    params = {
        "volume": 1,
        "chapter": "1"
    }
    
    try:
        response = requests.get(f"{API_URL}/search-by-reference", params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['count']} results for Volume 1, Chapter 1")
        else:
            print(f"❌ Reference search failed")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    print("=" * 60)
    print("🧪 BIHAR UL ANWAR RAG SYSTEM TEST")
    print("=" * 60)
    
    # Check system health
    try:
        health = requests.get(f"{API_URL}/")
        health_data = health.json()
        print(f"✅ System Status: {health_data['status']}")
        print(f"📚 Volumes in Database: {health_data['volumes_processed']}/110")
        print(f"📄 Total Chunks: {health_data['total_chunks']}")
        
        if health_data['volumes_processed'] == 0:
            print("\n⚠️  WARNING: No volumes processed yet!")
            print("Please run process_bihar_volumes.py first to process the PDFs")
            return
            
    except:
        print("❌ FastAPI server is not running!")
        print("Start the server first: python main.py")
        return
    
    # Run test queries
    print(f"\n🔄 Running {len(TEST_QUERIES)} test queries...")
    
    successful = 0
    failed = 0
    
    for query_data in TEST_QUERIES:
        if test_single_query(query_data):
            successful += 1
        else:
            failed += 1
        
        time.sleep(1)  # Small delay between queries
    
    # Test reference search
    test_reference_search()
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Successful Queries: {successful}/{len(TEST_QUERIES)}")
    print(f"❌ Failed Queries: {failed}/{len(TEST_QUERIES)}")
    
    if successful == len(TEST_QUERIES):
        print("\n🎉 All tests passed! System is working perfectly.")
    elif successful > 0:
        print("\n⚠️  Some tests passed. Check failed queries for issues.")
    else:
        print("\n❌ All tests failed. Check your setup.")
    
    print("\n💡 Access Swagger UI for interactive testing:")
    print("   http://localhost:8000/docs")

if __name__ == "__main__":
    main()