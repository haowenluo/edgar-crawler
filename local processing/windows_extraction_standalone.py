# ============================================================================
# STANDALONE WINDOWS EXTRACTION (No pathos dependency)
# ============================================================================
# This version doesn't use pathos/ppft - works on any system
# Copy this entire cell to replace Section 4 in your notebook
# ============================================================================

import time
import json
import os
import sys
import re
from tqdm import tqdm
from bs4 import BeautifulSoup

# Add repo to path
sys.path.insert(0, REPO_DIR)
from item_lists import item_list_10k

# Set recursion limit
sys.setrecursionlimit(30000)

# ============================================================================
# MINIMAL EXTRACTION CLASS (Standalone - no dependencies on pathos)
# ============================================================================

class SimpleExtractor:
    """Simplified extractor for Windows - no multiprocessing"""

    def __init__(self, items_to_extract, remove_tables=True):
        self.items_to_extract = items_to_extract
        self.remove_tables = remove_tables
        self.regex_flags = re.IGNORECASE | re.DOTALL | re.MULTILINE

    def strip_html(self, html_content):
        """Remove HTML tags using BeautifulSoup"""
        soup = BeautifulSoup(html_content, 'lxml')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

    def clean_text(self, text):
        """Clean and normalize text"""
        # Replace special characters
        text = text.replace('\xa0', ' ')
        text = text.replace('\x92', "'")
        text = text.replace('\x93', '"')
        text = text.replace('\x94', '"')
        text = text.replace('\x95', '•')
        text = text.replace('\x96', '-')
        text = text.replace('\x97', '-')
        text = text.replace('\x98', '˜')
        text = text.replace('\x99', '™')

        # Remove multiple newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)

        return text

    def remove_tables_from_text(self, text):
        """Remove tables from text based on character patterns"""
        if not self.remove_tables:
            return text

        lines = text.split('\n')
        filtered_lines = []

        for line in lines:
            if len(line) == 0:
                filtered_lines.append(line)
                continue

            # Count digits and spaces
            digit_count = sum(c.isdigit() for c in line)
            space_count = sum(c.isspace() for c in line)

            # If line has high ratio of digits or spaces, likely a table
            if digit_count / len(line) > 0.3 or space_count / len(line) > 0.6:
                continue

            filtered_lines.append(line)

        return '\n'.join(filtered_lines)

    def extract_item(self, text, item_number):
        """Extract a specific item from the text"""
        # Build regex pattern to find item
        # Match "Item X" or "Item X." or "Item X:" patterns
        item_pattern = rf"item\s*{re.escape(item_number)}[\s:\.]"

        # Find all matches
        matches = list(re.finditer(item_pattern, text, self.regex_flags))

        if not matches:
            return ""

        # Get first match position
        start_pos = matches[0].start()

        # Find next item to get end position
        # Look for "Item X" where X is any number greater than current item
        next_item_pattern = r"item\s*(\d+)[:\.\s]"
        next_matches = re.finditer(next_item_pattern, text[start_pos+10:], self.regex_flags)

        end_pos = len(text)
        current_item_num = int(item_number.replace('A', '').replace('B', '').replace('C', '')) if item_number[0].isdigit() else 99

        for match in next_matches:
            try:
                next_num_str = match.group(1)
                next_num = int(next_num_str.replace('A', '').replace('B', '').replace('C', ''))
                if next_num > current_item_num:
                    end_pos = start_pos + 10 + match.start()
                    break
            except:
                continue

        # Extract text between start and end
        item_text = text[start_pos:end_pos]

        return item_text.strip()

    def extract_items_from_filing(self, raw_html):
        """Extract all requested items from a filing"""
        # Strip HTML
        text = self.strip_html(raw_html)

        # Clean text
        text = self.clean_text(text)

        # Remove tables if requested
        text = self.remove_tables_from_text(text)

        # Extract each item
        extracted_data = {}

        for item_num in self.items_to_extract:
            item_key = f"item_{item_num.lower().replace('a', 'a').replace('b', 'b').replace('c', 'c')}"
            item_text = self.extract_item(text, item_num)
            extracted_data[item_key] = item_text

        return extracted_data

# ============================================================================
# MAIN PROCESSING LOOP
# ============================================================================

# Initialize processing summary
processing_summary = []

print("="*70)
print(" YEAR-BY-YEAR EXTRACTION (Windows Standalone - No pathos)")
print("="*70)
print(f"\nProcessing years: {YEAR_START} → {YEAR_END}")
print(f"Items to extract: {', '.join(ITEMS_TO_EXTRACT)}")
print(f"Download method: {DOWNLOAD_METHOD}")
print(f"⚠️  Note: Single-process extraction (Windows compatible)")
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

    # Step 5: Run extraction
    print(f"\n🚀 Step 5: Extract Items {', '.join(ITEMS_TO_EXTRACT)} for {year}")
    print(f"   This may take a while...\n")

    start_time = time.time()

    try:
        # Initialize extractor
        extractor = SimpleExtractor(
            items_to_extract=ITEMS_TO_EXTRACT,
            remove_tables=REMOVE_TABLES
        )

        # Get list of raw files to process
        raw_files = [f for f in os.listdir(raw_year_path)
                    if f.endswith(('.txt', '.htm', '.html'))]

        print(f"   Processing {len(raw_files):,} files...")

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

                # Read raw file
                input_path = os.path.join(raw_year_path, filename)
                with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_html = f.read()

                # Extract items
                extracted_data = extractor.extract_items_from_filing(raw_html)

                # Add metadata from filename
                parts = filename.replace('.htm', '').replace('.html', '').replace('.txt', '').split('_')
                if len(parts) >= 4:
                    extracted_data['cik'] = parts[0]
                    extracted_data['filing_type'] = '10-K'
                    extracted_data['year'] = parts[2]
                    extracted_data['accession_number'] = parts[3]

                # Save to JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(extracted_data, f, indent=2, ensure_ascii=False)

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
