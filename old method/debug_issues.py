# debug_issues.py - Debug the specific issues found in testing
import requests
import json

API_URL = "http://localhost:8000"

def debug_failed_queries():
    """Debug the two failed queries"""
    print("🔍 Debugging Failed Queries")
    print("=" * 50)
    
    failed_queries = [
        "What are the names of the Day of Judgment mentioned in Bihar ul Anwar?",
        "What Quranic verses about resurrection are mentioned in Bihar ul Anwar Volume 7?"
    ]
    
    for i, query in enumerate(failed_queries, 1):
        print(f"\n🐛 Debug Query {i}: {query[:50]}...")
        
        payload = {
            "query": query,
            "top_k": 3,
            "include_arabic": True,
            "volume_filter": 7
        }
        
        try:
            response = requests.post(f"{API_URL}/query", json=payload, timeout=60)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Success: {data.get('success')}")
                if not data.get('success'):
                    print(f"   Error: {data.get('error', 'No error message')}")
            else:
                print(f"   Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   Exception: {str(e)}")

def debug_reference_search():
    """Debug the reference search failure"""
    print("\n🔍 Debugging Reference Search")
    print("=" * 50)
    
    test_cases = [
        {"volume": 7},
        {"volume": 7, "chapter": "3"},
        {"volume": 7, "chapter": "10"}
    ]
    
    for test in test_cases:
        print(f"\n🧪 Testing: {test}")
        try:
            response = requests.get(f"{API_URL}/search-by-reference", params=test, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Results: {data.get('count', 0)}")
            else:
                print(f"   Error: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   Exception: {str(e)}")

def check_database_content():
    """Check what's actually in the database for Volume 7"""
    print("\n🔍 Checking Database Content")
    print("=" * 50)
    
    try:
        # Get statistics
        stats = requests.get(f"{API_URL}/statistics").json()
        print(f"📊 Database Stats:")
        print(f"   Total volumes: {stats['statistics']['total_volumes']}")
        print(f"   Total chunks: {stats['statistics']['total_chunks']}")
        
        # Get volumes list
        volumes = requests.get(f"{API_URL}/volumes").json()
        volume_7_info = [v for v in volumes['volumes'] if v['volume_number'] == 7]
        
        if volume_7_info:
            vol_7 = volume_7_info[0]
            print(f"\n📖 Volume 7 Info:")
            print(f"   Chunks: {vol_7['chunk_count']}")
            print(f"   Chapters: {vol_7['chapters']}")
            print(f"   Processed: {vol_7['processed_date']}")
        else:
            print("❌ Volume 7 not found in processed volumes")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")

def test_simple_query():
    """Test a very simple query to isolate issues"""
    print("\n🔍 Testing Simple Query")
    print("=" * 50)
    
    simple_payload = {
        "query": "resurrection",
        "top_k": 2,
        "include_arabic": False,
        "volume_filter": 7
    }
    
    try:
        response = requests.post(f"{API_URL}/query", json=simple_payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Sources: {data.get('total_sources', 0)}")
            if data.get('success'):
                print(f"Answer length: {len(data.get('answer', ''))}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

def main():
    print("🐛 DEBUGGING BIHAR UL ANWAR ISSUES")
    print("=" * 60)
    
    # Run all debug tests
    check_database_content()
    debug_reference_search()
    debug_failed_queries()
    test_simple_query()
    
    print("\n💡 NEXT STEPS RECOMMENDATIONS:")
    print("1. Check server logs for detailed error messages")
    print("2. Verify database connection and data integrity")
    print("3. Test with simpler queries first")
    print("4. Consider reprocessing Volume 7 if data issues found")

if __name__ == "__main__":
    main()