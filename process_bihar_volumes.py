# Optimized Batch Processor for Bihar ul Anwar
import os
import requests
import time
import json
from pathlib import Path
from tqdm import tqdm
import concurrent.futures
from typing import List, Dict

# Configuration
API_URL = "http://localhost:8000"
BIHAR_FOLDER = "Bihar_Al_Anwaar_PDFs"  # Your PDF folder
MAX_PAGES_PER_VOLUME = 200  # Limit pages for large files
CONCURRENT_VOLUMES = 1  # Process 'n' volumes simultaneously
RETRY_FAILED = True

def process_volume_with_retry(pdf_path: str, volume_number: int, max_retries: int = 2):
    """Process a single volume with retry logic"""
    url = f"{API_URL}/process-volume"
    
    payload = {
        "file_path": str(pdf_path),
        "volume_number": volume_number,
        "language": "mixed"
    }
    
    for attempt in range(max_retries + 1):
        try:
            # Shorter timeout for faster failure detection
            timeout = 300 if attempt == 0 else 600  # 5 min first try, 10 min retry
            
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("success"):
                return result
            else:
                return {"success": False, "error": result.get("error", "Unknown error")}
                
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                print(f"    ⏱️ Volume {volume_number} timeout, retrying... (attempt {attempt + 2})")
                continue
            return {"success": False, "error": "Processing timeout after retries"}
            
        except Exception as e:
            if attempt < max_retries:
                print(f"    🔄 Volume {volume_number} error, retrying... (attempt {attempt + 2})")
                time.sleep(5)  # Wait before retry
                continue
            return {"success": False, "error": str(e)}
    
    return {"success": False, "error": "Max retries exceeded"}

def get_processed_volumes():
    """Get list of already processed volumes"""
    try:
        response = requests.get(f"{API_URL}/volumes", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return set(v['volume_number'] for v in data.get('volumes', []))
    except:
        pass
    return set()

def process_volumes_optimized():
    """Optimized main processing function"""
    print("=" * 60)
    print("🚀 OPTIMIZED BIHAR UL ANWAR PROCESSOR")
    print("=" * 60)
    
    # Check API health
    try:
        health = requests.get(f"{API_URL}/", timeout=10)
        health_data = health.json()
        print(f"✅ API Status: {health_data['status']}")
        print(f"📊 Current volumes: {health_data['volumes_processed']}")
    except:
        print("❌ API server not reachable!")
        return
    
    # Find PDF files
    folder = Path(BIHAR_FOLDER)
    if not folder.exists():
        print(f"❌ Folder not found: {BIHAR_FOLDER}")
        return
    
    pdf_files = list(folder.glob("*.pdf"))
    print(f"📁 Found {len(pdf_files)} PDF files")
    
    # Get volume numbers and sort
    volume_files = []
    for pdf_file in pdf_files:
        try:
            # Extract volume number
            volume_num = int(pdf_file.stem.split('_V')[1])
            volume_files.append((volume_num, pdf_file))
        except:
            print(f"⚠️ Cannot determine volume number for: {pdf_file.name}")
    
    volume_files.sort(key=lambda x: x[0])
    print(f"📚 Identified {len(volume_files)} volumes")
    
    # Check already processed
    processed_volumes = get_processed_volumes()
    
    # ✅ CORRECT PLACEMENT: Filter for volumes 8-20 for testing
    pending_volumes = [(v, f) for v, f in volume_files if v not in processed_volumes and 8 <= v <= 20]
    
    print(f"✅ Already processed: {len(processed_volumes)} volumes")
    print(f"⏳ Testing with volumes 8-20: {len(pending_volumes)} volumes")
    
    if not pending_volumes:
        print("🎉 All test volumes (8-20) already processed!")
        return
    
    # Show which volumes will be processed
    test_volume_numbers = [v for v, f in pending_volumes]
    print(f"📋 Will process volumes: {test_volume_numbers}")
    
    # Process volumes with concurrent processing
    successful = []
    failed = []
    
    print(f"\n🔄 Processing {len(pending_volumes)} volumes...")
    print(f"⚡ Concurrent processing: {CONCURRENT_VOLUMES} volumes at once")
    print("-" * 60)
    
    # Process in batches for better resource management
    batch_size = CONCURRENT_VOLUMES
    
    for i in range(0, len(pending_volumes), batch_size):
        batch = pending_volumes[i:i + batch_size]
        batch_start_time = time.time()
        
        print(f"\n📦 Processing batch {i//batch_size + 1}: Volumes {[v for v, _ in batch]}")
        
        # Use ThreadPoolExecutor for concurrent processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Submit all volumes in batch
            future_to_volume = {
                executor.submit(process_volume_with_retry, pdf_path, volume_num): (volume_num, pdf_path)
                for volume_num, pdf_path in batch
            }
            
            # Process completed volumes
            for future in concurrent.futures.as_completed(future_to_volume):
                volume_num, pdf_path = future_to_volume[future]
                
                try:
                    result = future.result()
                    
                    if result.get("success"):
                        successful.append({
                            "volume": volume_num,
                            "chunks": result.get("chunks_created", 0),
                            "time": result.get("processing_time", 0)
                        })
                        print(f"    ✅ Volume {volume_num}: {result.get('chunks_created', 0)} chunks")
                    else:
                        failed.append({
                            "volume": volume_num,
                            "file": pdf_path.name,
                            "error": result.get("error", "Unknown error")
                        })
                        print(f"    ❌ Volume {volume_num}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    failed.append({
                        "volume": volume_num,
                        "file": pdf_path.name,
                        "error": f"Processing exception: {str(e)}"
                    })
                    print(f"    ❌ Volume {volume_num}: Exception - {str(e)}")
        
        batch_time = time.time() - batch_start_time
        print(f"    ⏱️ Batch completed in {batch_time/60:.1f} minutes")
        
        # Small break between batches
        if i + batch_size < len(pending_volumes):
            print("    😴 Resting 30 seconds before next batch...")
            time.sleep(30)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 PROCESSING SUMMARY")
    print("=" * 60)
    
    total_successful = len(successful)
    total_failed = len(failed)
    total_chunks = sum(s['chunks'] for s in successful)
    
    print(f"✅ Successful: {total_successful} volumes")
    print(f"❌ Failed: {total_failed} volumes")
    print(f"📝 Total chunks created: {total_chunks}")
    
    if successful:
        avg_time = sum(s['time'] for s in successful) / len(successful)
        avg_chunks = total_chunks / len(successful)
        print(f"⏱️ Average time per volume: {avg_time/60:.1f} minutes")
        print(f"📊 Average chunks per volume: {avg_chunks:.0f}")
    
    # Show failed volumes
    if failed:
        print(f"\n❌ Failed Volumes:")
        for fail in failed:
            print(f"    Volume {fail['volume']}: {fail['error'][:100]}...")
    
    # Get final statistics
    try:
        stats = requests.get(f"{API_URL}/statistics").json()
        print(f"\n📈 Final Database Stats:")
        print(f"    Volumes: {stats['statistics']['total_volumes']}/110")
        print(f"    Chunks: {stats['statistics']['total_chunks']}")
        print(f"    Coverage: {stats['coverage']}")
    except:
        pass
    
    # Save report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "successful": successful,
        "failed": failed,
        "summary": {
            "total_successful": total_successful,
            "total_failed": total_failed,
            "total_chunks": total_chunks
        }
    }
    
    report_file = f"bihar_processing_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved: {report_file}")
    
    # Suggest next steps
    if total_failed > 0 and RETRY_FAILED:
        print(f"\n🔄 To retry failed volumes, run this script again")
    
    print(f"\n🎯 Access the system at: {API_URL}/docs")

if __name__ == "__main__":
    process_volumes_optimized()