# quick_test.py - Fast test to verify system is working
import requests
import time

API_URL = "http://localhost:8000"

def quick_health_check():
    """Quick health check"""
    print("🏥 QUICK HEALTH CHECK")
    print("=" * 30)
    
    try:
        response = requests.get(f"{API_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API: {data['status']}")
            print(f"📊 Volumes: {data['volumes_processed']}")
            print(f"📝 Chunks: {data['total_chunks']}")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API not responding: {e}")
        return False

def quick_query_test():
    """Test a simple query"""
    print("\n🔍 QUICK QUERY TEST")
    print("=" * 30)
    
    payload = {
        "query": "What is knowledge?",
        "top_k": 3,
        "include_arabic": False,
        "volume_filter": 1
    }
    
    try:
        start = time.time()
        response = requests.post(f"{API_URL}/query", json=payload, timeout=60)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Query successful in {elapsed:.1f}s")
            print(f"📚 Sources: {data.get('total_sources', 0)}")
            
            # Show short answer
            answer = data.get('answer', '')[:200]
            print(f"💬 Answer: {answer}...")
            return True
        else:
            print(f"❌ Query failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Query error: {e}")
        return False

def quick_reference_test():
    """Test reference search with known data"""
    print("\n📖 QUICK REFERENCE TEST")  
    print("=" * 30)
    
    # We know chapter '1' exists from debug output
    params = {"volume": 1, "chapter": "1"}
    
    try:
        response = requests.get(f"{API_URL}/search-by-reference", params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f"✅ Reference search: {count} results")
            
            if count > 0:
                first = data['results'][0]
                print(f"📋 First result:")
                print(f"   Volume: {first.get('volume_number')}")
                print(f"   Chapter: {first.get('chapter_name')}")
                print(f"   Preview: {first.get('full_text', '')[:100]}...")
                return True
            else:
                print("⚠️ No results but no error")
                return False
        else:
            print(f"❌ Reference search failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Reference search timeout: {e}")
        return False

def main():
    print("⚡ BIHAR UL ANWAR QUICK TEST")
    print("=" * 40)
    
    # Run quick tests
    health_ok = quick_health_check()
    
    if health_ok:
        query_ok = quick_query_test()
        ref_ok = quick_reference_test()
        
        print(f"\n📊 QUICK TEST RESULTS")
        print("=" * 30)
        print(f"API Health: {'✅' if health_ok else '❌'}")
        print(f"Query System: {'✅' if query_ok else '❌'}")  
        print(f"Reference Search: {'✅' if ref_ok else '❌'}")
        
        if health_ok and query_ok:
            print("\n🎉 CORE SYSTEM IS WORKING!")
            print("Main search functionality is operational.")
            
            if not ref_ok:
                print("\n🔧 Reference search needs the quick fix.")
                print("Apply the database fix and restart server.")
        else:
            print("\n⚠️ Some issues detected. Check server status.")
    else:
        print("\n❌ Server not responding. Start the server first:")
        print("   python main.py")

if __name__ == "__main__":
    main()