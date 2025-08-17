# process_bihar_volumes.py - Batch processor for Bihar ul Anwar 110 volumes

import os
import re
import requests
from pathlib import Path
from tqdm import tqdm
import time
import json

# Configuration
API_URL = "http://localhost:8000"
BIHAR_FOLDER = "Bihar_Al_Anwaar_PDFs/"  # Update this path to your Bihar ul Anwar folder

def process_single_volume(pdf_path: str, volume_number: int):
    """Process a single Bihar ul Anwar volume"""
    url = f"{API_URL}/process-volume"
    
    payload = {
        "file_path": str(pdf_path),
        "volume_number": volume_number,
        "language": "mixed"  # Arabic + English
    }
    
    try:
        response = requests.post(url, json=payload, timeout=300)  # 5 min timeout
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Processing timeout - file too large"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def extract_volume_number(filename: str) -> int:
    """Extract volume number from filename"""
    # Try different patterns
    patterns = [
        r'vol(?:ume)?[_\s-]?(\d+)',  # vol_1, volume_1, vol-1
        r'v(\d+)',  # v1, v01
        r'(\d+)',  # just numbers
        r'bihar[_\s-]?(\d+)'  # bihar_1, bihar-1
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename.lower())
        if match:
            return int(match.group(1))
    
    return None

def main():
    """Process all Bihar ul Anwar volumes"""
    print("=" * 60)
    print("📚 BIHAR UL ANWAR BATCH PROCESSOR")
    print("Processing 110 Volumes of Shia Hadith Collection")
    print("=" * 60)
    
    # Check API health
    try:
        health = requests.get(f"{API_URL}/")
        print(f"✅ API Status: {health.json()['status']}")
        print(f"📊 Current volumes in database: {health.json()['volumes_processed']}")
    except:
        print("❌ ERROR: FastAPI server is not running!")
        print("Please start the server first: python main.py")
        return
    
    # Find PDF files
    folder = Path(BIHAR_FOLDER)
    if not folder.exists():
        print(f"❌ Folder not found: {BIHAR_FOLDER}")
        print("Please update BIHAR_FOLDER path in this script")
        return
    
    pdf_files = list(folder.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {BIHAR_FOLDER}")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF files")
    
    # Sort files by volume number
    volume_files = []
    for pdf_file in pdf_files:
        volume_num = extract_volume_number(pdf_file.stem)
        if volume_num:
            volume_files.append((volume_num, pdf_file))
        else:
            print(f"⚠️  Cannot determine volume number for: {pdf_file.name}")
    
    volume_files.sort(key=lambda x: x[0])
    
    print(f"📚 Identified {len(volume_files)} Bihar ul Anwar volumes")
    
    # Check which volumes are already processed
    try:
        volumes_response = requests.get(f"{API_URL}/volumes")
        processed_volumes = [v['volume_number'] for v in volumes_response.json()['volumes']]
        print(f"✅ Already processed volumes: {processed_volumes[:10]}..." if len(processed_volumes) > 10 else processed_volumes)
    except:
        processed_volumes = []
    
    # Process each volume
    successful = []
    failed = []
    skipped = []
    
    print("\n🔄 Starting processing...")
    print("-" * 40)
    
    for volume_num, pdf_file in tqdm(volume_files, desc="Processing volumes"):
        # Skip if already processed
        if volume_num in processed_volumes:
            skipped.append(volume_num)
            continue
        
        print(f"\n📖 Processing Volume {volume_num}: {pdf_file.name}")
        
        result = process_single_volume(pdf_file, volume_num)
        
        if result.get("success"):
            successful.append({
                "volume": volume_num,
                "chunks": result.get("chunks_created", 0)
            })
            print(f"   ✅ Success: {result.get('chunks_created', 0)} chunks created")
        else:
            failed.append({
                "volume": volume_num,
                "file": pdf_file.name,
                "error": result.get("error", "Unknown error")
            })
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        
        # Small delay between volumes
        time.sleep(1)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 PROCESSING SUMMARY")
    print("=" * 60)
    
    print(f"✅ Successfully processed: {len(successful)} volumes")
    if successful:
        total_chunks = sum(v['chunks'] for v in successful)
        print(f"   Total chunks created: {total_chunks}")
        print(f"   Volumes: {[v['volume'] for v in successful[:10]]}..." if len(successful) > 10 else [v['volume'] for v in successful])
    
    if skipped:
        print(f"⏭️  Skipped (already processed): {len(skipped)} volumes")
    
    if failed:
        print(f"❌ Failed: {len(failed)} volumes")
        for fail in failed[:5]:
            print(f"   - Volume {fail['volume']}: {fail['error']}")
    
    # Get final statistics
    try:
        stats = requests.get(f"{API_URL}/statistics").json()
        print("\n📈 FINAL DATABASE STATISTICS:")
        print(f"   Total Volumes: {stats['statistics']['total_volumes']}/110")
        print(f"   Total Chunks: {stats['statistics']['total_chunks']}")
        print(f"   Total Chapters: {stats['statistics']['total_chapters']}")
        print(f"   Total Hadiths: {stats['statistics']['total_hadiths']}")
        print(f"   Coverage: {stats['coverage']}")
    except:
        pass
    
    # Save processing report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "successful": successful,
        "failed": failed,
        "skipped": skipped,
        "total_processed": len(successful),
        "total_failed": len(failed),
        "total_skipped": len(skipped)
    }
    
    report_file = f"bihar_processing_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📝 Processing report saved to: {report_file}")
    
    # Suggest next steps
    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS:")
    print("=" * 60)
    if len(successful) + len(skipped) == 110:
        print("✅ All 110 volumes processed successfully!")
        print("You can now query the system at http://localhost:8000/docs")
        print("\nExample queries to try:")
        print('- "What are the traditions about the creation of Prophet Muhammad?"')
        print('- "Find hadiths about Imam Ali in Karbala"')
        print('- "What does Bihar ul Anwar say about the signs of Imam Mahdi?"')
    else:
        missing = 110 - (len(successful) + len(skipped))
        print(f"⚠️  {missing} volumes still need to be processed")
        print("Check the failed volumes and try processing them individually")
    
    print("\n💡 TIP: Use the Swagger UI at http://localhost:8000/docs to test queries")

if __name__ == "__main__":
    main()