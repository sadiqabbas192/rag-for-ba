# test_single_volume.py - Test processing a single volume (Updated for refactored code)
import requests
import time
from pathlib import Path

API_URL = "http://localhost:8000"
BIHAR_FOLDER = "Bihar_Al_Anwaar_PDFs"

def test_single_volume(volume_number: int = 1):
    """Test processing a single volume"""
    print(f"🧪 Testing Volume {volume_number} processing...")
    
    # Check if PDF exists
    pdf_path = Path(BIHAR_FOLDER) / f"BiharAlAnwaar_V{volume_number}.pdf"
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return False
    
    print(f"📁 Found PDF: {pdf_path}")
    print(f"📊 File size: {pdf_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    # Check API health
    try:
        health = requests.get(f"{API_URL}/")
        if health.status_code != 200:
            print("❌ API not responding")
            return False
        
        health_data = health.json()
        print("✅ API is healthy")
        print(f"📊 Current volumes: {health_data.get('volumes_processed', 0)}")
        print(f"📝 Current chunks: {health_data.get('total_chunks', 0)}")
        
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return False
    
    # Process the volume
    payload = {
        "file_path": str(pdf_path),
        "volume_number": volume_number,
        "language": "mixed"
    }
    
    print(f"🔄 Starting processing...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_URL}/process-volume", 
            json=payload, 
            timeout=600  # 10 minutes max
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                print(f"✅ Success! Volume {volume_number} processed")
                print(f"   📝 Chunks created: {result.get('chunks_created', 0)}")
                print(f"   ⏱️ Processing time: {elapsed/60:.1f} minutes")
                print(f"   📄 Pages processed: {result.get('pages_processed', 'Unknown')}")
                return True
            else:
                print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"⏱️ Timeout after {elapsed/60:.1f} minutes")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error after {elapsed/60:.1f} minutes: {str(e)}")
        return False

def test_query_system():
    """Test if we can query the processed data"""
    print(f"\n🔍 Testing query system...")
    
    payload = {
        "query": "What are the traditions about Prophet Muhammad?",
        "top_k": 3,
        "include_arabic": True
    }
    
    try:
        response = requests.post(f"{API_URL}/query", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                print(f"✅ Query successful!")
                print(f"   📚 Found {result.get('total_sources', 0)} sources")
                print(f"   ⏱️ Query time: {result.get('processing_time', 0):.2f} seconds")
                
                # Show answer preview
                answer = result.get('answer', '')
                preview = answer[:200] + "..." if len(answer) > 200 else answer
                print(f"   💬 Answer preview: {preview}")
                
                # Show first reference
                references = result.get('references', [])
                if references:
                    ref = references[0]
                    print(f"   📖 First reference: Volume {ref.get('volume')}, Chapter {ref.get('chapter')}")
                
                return True
            else:
                print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Query API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Query error: {str(e)}")
        return False

def show_system_stats():
    """Show current system statistics"""
    try:
        print(f"\n📊 System Statistics:")
        
        # Get statistics
        stats_response = requests.get(f"{API_URL}/statistics")
        if stats_response.status_code == 200:
            stats = stats_response.json()['statistics']
            print(f"   📚 Volumes processed: {stats['total_volumes']}/110")
            print(f"   📝 Total chunks: {stats['total_chunks']}")
            print(f"   📖 Total chapters: {stats['total_chapters']}")
            print(f"   📜 Total hadiths: {stats['total_hadiths']}")
            print(f"   🔤 Arabic chunks: {stats['chunks_with_arabic']}")
            print(f"   🔡 English chunks: {stats['chunks_with_english']}")
        
        # Get volumes list
        volumes_response = requests.get(f"{API_URL}/volumes")
        if volumes_response.status_code == 200:
            volumes_data = volumes_response.json()
            processed_volumes = [v['volume_number'] for v in volumes_data['volumes']]
            missing_volumes = volumes_data['missing_volumes'][:10]  # Show first 10 missing
            
            print(f"   ✅ Processed volumes: {processed_volumes[:10]}..." if len(processed_volumes) > 10 else processed_volumes)
            if missing_volumes:
                print(f"   ❌ Missing volumes: {missing_volumes}...")
        
    except Exception as e:
        print(f"   ⚠️ Could not fetch statistics: {e}")

def main():
    print("=" * 60)
    print("🧪 BIHAR UL ANWAR - SINGLE VOLUME TEST (Refactored)")
    print("=" * 60)
    
    # Show initial stats
    show_system_stats()
    
    # Test volume 1 first (usually smaller)
    print(f"\n" + "=" * 40)
    success = test_single_volume(volume_number=1)
    
    if success:
        print(f"\n🎉 Volume processing successful!")
        
        # Test the query system
        query_success = test_query_system()
        
        if query_success:
            print(f"\n✅ Full system test PASSED!")
            print(f"🚀 You can now run the batch processor:")
            print(f"   python process_bihar_volumes.py")
        else:
            print(f"\n⚠️ Query system needs attention")
            
        # Show updated stats
        show_system_stats()
        
    else:
        print(f"\n❌ Volume processing failed!")
        print(f"🔧 Check your setup:")
        print(f"   1. Ensure all files are in correct structure:")
        print(f"      - main.py")
        print(f"      - config.py") 
        print(f"      - database.py")
        print(f"      - processing.py")
        print(f"   2. Check PostgreSQL is running")
        print(f"   3. Verify .env file has correct settings")
        print(f"   4. Check Google API key is valid")

if __name__ == "__main__":
    main()