# test_volume_7_queries.py - Test specific queries based on Volume 7 content
import requests
import json
import time

API_URL = "http://localhost:8000"

# Test queries based on actual Volume 7 content
VOLUME_7_TEST_QUERIES = [
    {
        "query": "What does Bihar ul Anwar say about proof of resurrection?",
        "description": "Testing Chapter 3 content about resurrection proof",
        "expected_volume": 7,
        "expected_content": ["resurrection", "revival", "dead", "Allah"]
    },
    {
        "query": "What are the names of the Day of Judgment mentioned in Bihar ul Anwar?", 
        "description": "Testing Chapter 4 content about Day of Judgment names",
        "expected_volume": 7,
        "expected_content": ["judgment", "day", "reckoning", "din"]
    },
    {
        "query": "What does Bihar ul Anwar say about the plains of Mahshar?",
        "description": "Testing Chapter 5 content about Mahshar description",
        "expected_volume": 7,
        "expected_content": ["mahshar", "plains", "gathering"]
    },
    {
        "query": "How does Bihar ul Anwar describe the situation of pious ones on judgment day?",
        "description": "Testing Chapter 8 content about pious people",
        "expected_volume": 7,
        "expected_content": ["pious", "criminals", "judgment", "day"]
    },
    {
        "query": "What does Bihar ul Anwar say about people being called by their mothers' names?",
        "description": "Testing Chapter 9 content about lineage on judgment day",
        "expected_volume": 7,
        "expected_content": ["mothers", "names", "shias", "lineage", "rasool"]
    },
    {
        "query": "What does Bihar ul Anwar mention about the Scale (Mizan) on judgment day?",
        "description": "Testing Chapter 10 content about the Scale",
        "expected_volume": 7,
        "expected_content": ["scale", "mizan", "weighing"]
    },
    {
        "query": "What Quranic verses about resurrection are mentioned in Bihar ul Anwar Volume 7?",
        "description": "Testing Quranic references in Chapter 3",
        "expected_volume": 7,
        "expected_content": ["quran", "verses", "surah", "baqarah", "fatiha"]
    }
]

def test_volume_7_query(query_data, include_arabic=True):
    """Test a single query against Volume 7 content"""
    print(f"\n{'='*60}")
    print(f"🔍 Testing: {query_data['description']}")
    print(f"❓ Query: {query_data['query']}")
    print("-" * 40)
    
    payload = {
        "query": query_data["query"],
        "top_k": 5,
        "include_arabic": include_arabic,
        "volume_filter": 7  # Filter to Volume 7 only
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{API_URL}/query", json=payload, timeout=30)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                print(f"✅ Query successful in {elapsed:.2f} seconds")
                print(f"📚 Found {data['total_sources']} relevant sources")
                
                # Check if results are from Volume 7
                references = data.get('references', [])
                volume_7_refs = [ref for ref in references if ref.get('volume') == 7]
                
                print(f"📖 Volume 7 references: {len(volume_7_refs)}/{len(references)}")
                
                # Show answer preview
                answer = data['answer']
                answer_preview = answer[:300] + "..." if len(answer) > 300 else answer
                print(f"\n💬 Answer Preview:")
                print(f"   {answer_preview}")
                
                # Show Volume 7 references
                if volume_7_refs:
                    print(f"\n📋 Volume 7 References:")
                    for i, ref in enumerate(volume_7_refs[:3], 1):
                        chapter = ref.get('chapter', 'Not specified')
                        hadith = ref.get('hadith_number', 'Not specified')
                        similarity = ref.get('similarity_score', 0)
                        
                        print(f"   {i}. Volume {ref['volume']}, Chapter {chapter}, Hadith {hadith}")
                        print(f"      Similarity: {similarity:.3f}")
                        
                        # Show excerpt
                        excerpt = ref.get('excerpt_english', '')[:150]
                        if excerpt:
                            print(f"      Excerpt: {excerpt}...")
                
                # Check for expected content
                answer_lower = answer.lower()
                expected_found = []
                for expected in query_data.get('expected_content', []):
                    if expected.lower() in answer_lower:
                        expected_found.append(expected)
                
                if expected_found:
                    print(f"\n✅ Expected content found: {expected_found}")
                else:
                    print(f"\n⚠️ Expected content not found in answer")
                
                return {
                    "success": True,
                    "volume_7_refs": len(volume_7_refs),
                    "total_refs": len(references),
                    "response_time": elapsed,
                    "expected_found": expected_found
                }
                
            else:
                print(f"❌ Query failed: {data.get('error', 'Unknown error')}")
                return {"success": False, "error": data.get('error')}
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout after 30 seconds")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"success": False, "error": str(e)}

def test_reference_search():
    """Test searching by specific Volume 7 reference"""
    print(f"\n{'='*60}")
    print("🔍 Testing Reference Search for Volume 7")
    print("-" * 40)
    
    # Test searching for Chapter 3 (Proof of Resurrection)
    params = {
        "volume": 7,
        "chapter": "3"
    }
    
    try:
        response = requests.get(f"{API_URL}/search-by-reference", params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Reference search successful")
            print(f"📖 Found {data['count']} results for Volume 7, Chapter 3")
            
            if data['count'] > 0:
                # Show first result
                first_result = data['results'][0]
                print(f"\n📋 First Result:")
                print(f"   Volume: {first_result.get('volume_number')}")
                print(f"   Chapter: {first_result.get('chapter_name', 'Not specified')}")
                print(f"   Hadith: {first_result.get('hadith_number', 'Not specified')}")
                
                # Show text preview
                english_text = first_result.get('english_text', '')[:200]
                if english_text:
                    print(f"   English preview: {english_text}...")
                
                arabic_text = first_result.get('arabic_text', '')[:100]
                if arabic_text:
                    print(f"   Arabic preview: {arabic_text}...")
            
            return True
        else:
            print(f"❌ Reference search failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Reference search error: {str(e)}")
        return False

def main():
    print("=" * 80)
    print("🧪 BIHAR UL ANWAR VOLUME 7 CONTENT TEST")
    print("Testing specific content from Volume 7 about Resurrection & Judgment Day")
    print("=" * 80)
    
    # Check API health
    try:
        health = requests.get(f"{API_URL}/")
        health_data = health.json()
        print(f"✅ API Status: {health_data['status']}")
        print(f"📊 Total volumes: {health_data['volumes_processed']}")
        print(f"📝 Total chunks: {health_data['total_chunks']}")
    except:
        print("❌ API not accessible! Make sure server is running.")
        return
    
    # Test all Volume 7 queries
    results = []
    successful_queries = 0
    
    for i, query_data in enumerate(VOLUME_7_TEST_QUERIES, 1):
        print(f"\n🔄 Test {i}/{len(VOLUME_7_TEST_QUERIES)}")
        result = test_volume_7_query(query_data)
        results.append(result)
        
        if result.get("success"):
            successful_queries += 1
        
        # Small delay between queries
        time.sleep(1)
    
    # Test reference search
    print(f"\n🔄 Testing Reference Search...")
    ref_search_success = test_reference_search()
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 VOLUME 7 TEST SUMMARY")
    print("=" * 80)
    
    print(f"✅ Successful queries: {successful_queries}/{len(VOLUME_7_TEST_QUERIES)}")
    print(f"✅ Reference search: {'Passed' if ref_search_success else 'Failed'}")
    
    if successful_queries > 0:
        # Calculate averages
        successful_results = [r for r in results if r.get("success")]
        avg_response_time = sum(r["response_time"] for r in successful_results) / len(successful_results)
        total_volume_7_refs = sum(r.get("volume_7_refs", 0) for r in successful_results)
        
        print(f"⏱️ Average response time: {avg_response_time:.2f} seconds")
        print(f"📖 Total Volume 7 references found: {total_volume_7_refs}")
        
        # Check content quality
        content_quality = sum(len(r.get("expected_found", [])) for r in successful_results)
        print(f"🎯 Content quality score: {content_quality}/{len(VOLUME_7_TEST_QUERIES) * 3}")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    if successful_queries == len(VOLUME_7_TEST_QUERIES) and ref_search_success:
        print("✅ All tests passed! Your system is working excellently.")
        print("🚀 Ready to run full batch processing: python process_bihar_volumes.py")
    elif successful_queries >= len(VOLUME_7_TEST_QUERIES) * 0.8:
        print("✅ Most tests passed! System is working well.")
        print("🔧 Minor issues detected but system is ready for batch processing.")
    else:
        print("⚠️ Some issues detected. Review failed queries before batch processing.")
    
    print(f"\n💡 Test Details:")
    for i, (query, result) in enumerate(zip(VOLUME_7_TEST_QUERIES, results), 1):
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        print(f"   {i}. {query['description'][:50]}... {status}")

if __name__ == "__main__":
    main()