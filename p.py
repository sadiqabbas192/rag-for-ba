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
    
    # Rest of the code continues...