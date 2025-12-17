# ============================================================================
# WINDOWS-COMPATIBLE EXTRACTION (Use this instead of original Section 4)
# ============================================================================
# This version uses the ExtractItems class directly instead of subprocess
# Works better on Windows with Jupyter notebooks
# ============================================================================

import time
import json
import os
import sys
from tqdm import tqdm

# Import the extraction module
sys.path.insert(0, REPO_DIR)
from extract_items import ExtractItems

# Initialize processing summary
processing_summary = []

print("="*70)
print(" YEAR-BY-YEAR EXTRACTION (Windows Compatible)")
print("="*70)
print(f"\nProcessing years: {YEAR_START} → {YEAR_END}")
print(f"Items to extract: {', '.join(ITEMS_TO_EXTRACT)}")
print(f"Download method: {DOWNLOAD_METHOD}")
print(f"⚠️  Note: Using single-process extraction (Windows compatible)")
print(f"\n" + "="*70)

# Generate year list (newest to oldest)
years_to_process = list(range(YEAR_START, YEAR_END - 1, -1))

for idx, year in enumerate(years_to_process):
    print(f"\n\n{'='*70}")
    print(f" PROCESSING YEAR: {year} ({idx + 1}/{len(years_to_process)})")
    print(f"{'='*70}\n")

    # Step 1: Check disk space
    print("📊 Step 1: Check disk space")
    if not print_disk_space():
        response = input("\n⚠️  Low disk space! Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("\n⏸️  Processing paused. Transfer files to SSD and resume.")
            break

    # Step 2: Check if raw files exist
    print(f"\n📂 Step 2: Check raw files for {year}")
    files_exist, num_raw_files = check_year_files_exist(year)

    if files_exist:
        print(f"   ✅ Found {num_raw_files:,} raw 10-K files for {year}")
    else:
        print(f"   ❌ No raw files found for {year}")

        if DOWNLOAD_METHOD == "rclone":
            # Download using rclone
            success = download_year_with_rclone(year)
            if not success:
                print(f"\n⚠️  Skipping {year} - download failed")
                processing_summary.append({
                    'year': year,
                    'status': 'failed',
                    'reason': 'download_failed'
                })
                continue
            files_exist, num_raw_files = check_year_files_exist(year)
        else:
            # Manual download
            print(f"\n   📥 Please download {year} folder from Google Drive:")
            print(f"      From: My Drive/EDGAR_Project/edgar_crawler/datasets/RAW_FILINGS/10-K/{year}/")
            print(f"      To: {os.path.join(LOCAL_RAW_FILINGS_DIR, str(year))}/")

            response = input(f"\n   Have you downloaded {year} files? (yes/skip): ")
            if response.lower() != 'yes':
                print(f"\n   ⏭️  Skipping {year}")
                processing_summary.append({
                    'year': year,
                    'status': 'skipped',
                    'reason': 'manual_download_not_ready'
                })
                continue

            files_exist, num_raw_files = check_year_files_exist(year)
            if not files_exist:
                print(f"   ❌ Still no files found. Skipping {year}")
                processing_summary.append({
                    'year': year,
                    'status': 'skipped',
                    'reason': 'files_not_found'
                })
                continue

    # Step 3: Check extraction status
    print(f"\n🔍 Step 3: Check extraction status for {year}")
    num_extracted = count_extracted_files(year)
    print(f"   Already extracted: {num_extracted:,} files")
    print(f"   Raw files: {num_raw_files:,} files")

    if num_extracted > 0:
        print(f"   ℹ️  Extraction will skip already-extracted files")

    # Step 4: Set up extraction
    print(f"\n⚙️  Step 4: Configure extraction for {year}")

    raw_year_path = os.path.join(LOCAL_RAW_FILINGS_DIR, str(year))
    extracted_year_path = os.path.join(LOCAL_EXTRACTED_DIR, str(year))
    os.makedirs(extracted_year_path, exist_ok=True)

    # Step 5: Run extraction using ExtractItems class directly
    print(f"\n🚀 Step 5: Extract Items {', '.join(ITEMS_TO_EXTRACT)} for {year}")
    print(f"   This may take a while...\n")

    start_time = time.time()

    try:
        # Initialize extractor
        extractor = ExtractItems(
            filing_types=['10-K'],
            items_to_extract=ITEMS_TO_EXTRACT,
            remove_tables=REMOVE_TABLES,
            skip_extracted_filings=True
        )

        # Get list of raw files to process
        raw_files = [f for f in os.listdir(raw_year_path)
                    if f.endswith(('.txt', '.htm', '.html'))]

        print(f"   Processing {len(raw_files)} files...")

        # Process each file
        extracted_count = 0
        skipped_count = 0
        error_count = 0

        for filename in tqdm(raw_files, desc=f"Extracting {year}"):
            try:
                # Generate output filename
                json_filename = os.path.splitext(filename)[0] + '.json'
                output_path = os.path.join(extracted_year_path, json_filename)

                # Skip if already exists
                if os.path.exists(output_path):
                    skipped_count += 1
                    continue

                # Extract items from this filing
                input_path = os.path.join(raw_year_path, filename)

                # Read raw file
                with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_text = f.read()

                # Extract items
                extracted_data = extractor.extract_items(raw_text, '10-K')

                # Parse filename to get metadata (CIK, year, accession)
                parts = filename.replace('.htm', '').replace('.html', '').replace('.txt', '').split('_')
                if len(parts) >= 4:
                    extracted_data['cik'] = parts[0]
                    extracted_data['filing_type'] = '10-K'

                # Save to JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(extracted_data, f, indent=2)

                extracted_count += 1

            except Exception as e:
                error_count += 1
                if error_count <= 5:  # Show first 5 errors
                    print(f"\n⚠️  Error processing {filename}: {e}")

        elapsed = time.time() - start_time

        print(f"\n✅ Extraction complete for {year}!")
        print(f"   Time elapsed: {elapsed/60:.1f} minutes")
        print(f"   Extracted: {extracted_count:,} files")
        print(f"   Skipped (already done): {skipped_count:,} files")
        if error_count > 0:
            print(f"   Errors: {error_count:,} files")

    except Exception as e:
        print(f"\n❌ Extraction failed for {year}: {e}")
        import traceback
        traceback.print_exc()
        processing_summary.append({
            'year': year,
            'status': 'failed',
            'reason': 'extraction_error',
            'error': str(e)
        })
        continue

    # Step 6: Verify results
    print(f"\n📊 Step 6: Verify extraction results for {year}")
    stats = get_extraction_stats(year)

    print(f"\n   Extraction Statistics:")
    print(f"   {'─'*50}")
    print(f"   Total extracted files: {stats['total_files']:,}")
    print(f"   With Item 1 (Business): {stats['has_item_1']:,}")
    print(f"   With Item 1A (Risk Factors): {stats['has_item_1a']:,}")
    print(f"   With Item 7 (MD&A): {stats['has_item_7']:,}")
    print(f"   With ALL three items: {stats['has_all_three']:,}")

    processing_summary.append({
        'year': year,
        'status': 'completed',
        'num_files': stats['total_files'],
        'elapsed_minutes': elapsed/60,
        'stats': stats
    })

    # Step 7: Confirm before next year (if enabled)
    if CONFIRM_BEFORE_NEXT_YEAR and idx < len(years_to_process) - 1:
        next_year = years_to_process[idx + 1]
        print(f"\n{'='*70}")
        print(f" YEAR {year} COMPLETE")
        print(f"{'='*70}")

        response = input(f"\n▶️  Continue to {next_year}? (yes/no/pause): ")

        if response.lower() == 'no':
            print(f"\n⏹️  Stopping. You can resume later by re-running this cell.")
            break
        elif response.lower() == 'pause':
            print(f"\n⏸️  Paused. Run this cell again to continue.")
            break

    print(f"\n✅ Year {year} processing complete!\n")

print(f"\n\n{'='*70}")
print(" PROCESSING SUMMARY")
print(f"{'='*70}\n")

for entry in processing_summary:
    year = entry['year']
    status = entry['status']

    if status == 'completed':
        print(f"✅ {year}: {entry['num_files']:,} files in {entry['elapsed_minutes']:.1f} min")
    elif status == 'failed':
        print(f"❌ {year}: Failed - {entry.get('reason', 'unknown')}")
        if 'error' in entry:
            print(f"    Error: {entry['error']}")
    elif status == 'skipped':
        print(f"⏭️  {year}: Skipped - {entry['reason']}")

print(f"\n{'='*70}")
