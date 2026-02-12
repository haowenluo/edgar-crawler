#!/usr/bin/env python3
"""
Year-by-Year 10-K Extraction Script
Extracts Items 1, 1A, and 7 from SEC 10-K filings using the ExtractItems class.

This script processes files year by year (2025 → 2010) and saves extracted items as JSON files.
It uses the ExtractItems class from extract_items.py but works in single-process mode (no pathos required).
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add the repository root to the path
REPO_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_DIR))

try:
    from extract_items import ExtractItems
    from item_lists import item_list_10k
except ImportError as e:
    print(f"ERROR: Error importing required modules: {e}")
    print(f"   Make sure you're running this from the edgar-crawler repository")
    print(f"   Repository path: {REPO_DIR}")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths
RAW_FILINGS_DIR = r"C:\Users\luh\OneDrive - purdue.edu\10k extraction\Raw 10K"
EXTRACTED_DIR = r"C:\Users\luh\OneDrive - purdue.edu\10k extraction\extracted files\MDA and item1"

# Items to extract
ITEMS_TO_EXTRACT = ["1", "1A", "7"]

# Extraction settings
REMOVE_TABLES = True
SKIP_EXTRACTED = True

# Year range (newest to oldest)
YEAR_START = 2023
YEAR_END = 2018 # Process only 2024 (set to 2009 for full range 2024→2010)

# Processing options
CONFIRM_BEFORE_NEXT_YEAR = False  # Set to True to confirm before each year

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_filename(filename: str) -> Optional[Dict[str, str]]:
    """
    Parse a 10-K filename to extract metadata.
    
    Expected format: {cik}_10K_{year}_{accession}.{ext}
    Example: 1002135_10K_2023_0000914760-23-000052.htm
    """
    # Remove extension
    base_name = filename.rsplit('.', 1)[0]
    
    # Try to match the pattern
    pattern = r'^(\d+)_10K_(\d{4})_(.+)$'
    match = re.match(pattern, base_name)
    
    if match:
        cik = match.group(1)
        year = match.group(2)
        accession = match.group(3)
        
        return {
            'cik': cik,
            'year': year,
            'accession': accession,
            'filename': filename
        }
    
    return None


def create_filing_metadata(file_info: Dict[str, str], raw_file_path: str) -> Dict[str, Any]:
    """
    Create a filing_metadata dictionary for ExtractItems.
    
    ExtractItems expects specific fields. We'll create minimal metadata
    since we're working with raw files directly.
    """
    return {
        "CIK": file_info['cik'],
        "Company": f"Company_{file_info['cik']}",  # We don't have company name from filename
        "Type": "10-K",
        "Date": f"{file_info['year']}-12-31",  # Approximate date
        "Period of Report": f"{file_info['year']}-12-31",
        "SIC": "",
        "State of Inc": "",
        "State location": "",
        "Fiscal Year End": f"{file_info['year']}-12-31",
        "html_index": "",
        "htm_file_link": "",
        "complete_text_file_link": "",
        "filename": file_info['filename']
    }


def extract_items_from_file(
    extractor: ExtractItems,
    raw_file_path: str,
    file_info: Dict[str, str]
) -> Optional[Dict[str, Any]]:
    """
    Extract items from a single file using ExtractItems.
    
    ExtractItems now supports year-based directory structure (we modified it),
    so we can use it directly.
    """
    try:
        # Create filing metadata
        filing_metadata = create_filing_metadata(file_info, raw_file_path)
        
        # ExtractItems will now search in year directories automatically
        # since we modified extract_items.py to support this structure
        json_content = extractor.extract_items(filing_metadata)
        
        # Filter to only include requested items
        if json_content:
            filtered_content = {
                "cik": json_content.get("cik", file_info['cik']),
                "company": json_content.get("company", f"Company_{file_info['cik']}"),
                "filing_type": "10-K",
                "year": file_info['year'],
                "item_1": json_content.get("item_1", ""),
                "item_1a": json_content.get("item_1A", ""),
                "item_7": json_content.get("item_7", "")
            }
            return filtered_content
        
        return None
        
    except Exception as e:
        print(f"   WARNING: Error extracting from {file_info['filename']}: {e}")
        return None


def count_files_in_year(year: int) -> int:
    """Count raw files for a given year."""
    year_dir = os.path.join(RAW_FILINGS_DIR, str(year))
    if not os.path.exists(year_dir):
        return 0
    
    files = [f for f in os.listdir(year_dir) 
             if f.endswith(('.htm', '.html', '.txt'))]
    return len(files)


def count_extracted_files(year: int) -> int:
    """Count already extracted files for a given year."""
    year_dir = os.path.join(EXTRACTED_DIR, str(year))
    if not os.path.exists(year_dir):
        return 0
    
    files = [f for f in os.listdir(year_dir) if f.endswith('.json')]
    return len(files)


def get_extraction_stats(year: int) -> Dict[str, int]:
    """Get statistics about extracted files for a year."""
    year_dir = os.path.join(EXTRACTED_DIR, str(year))
    if not os.path.exists(year_dir):
        return {
            'total_files': 0,
            'has_item_1': 0,
            'has_item_1a': 0,
            'has_item_7': 0,
            'has_all_three': 0
        }
    
    stats = {
        'total_files': 0,
        'has_item_1': 0,
        'has_item_1a': 0,
        'has_item_7': 0,
        'has_all_three': 0
    }
    
    for filename in os.listdir(year_dir):
        if filename.endswith('.json'):
            stats['total_files'] += 1
            filepath = os.path.join(year_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    has_1 = bool(data.get('item_1', '').strip())
                    has_1a = bool(data.get('item_1a', '').strip())
                    has_7 = bool(data.get('item_7', '').strip())
                    
                    if has_1:
                        stats['has_item_1'] += 1
                    if has_1a:
                        stats['has_item_1a'] += 1
                    if has_7:
                        stats['has_item_7'] += 1
                    if has_1 and has_1a and has_7:
                        stats['has_all_three'] += 1
            except:
                pass
    
    return stats


# ============================================================================
# MAIN EXTRACTION FUNCTION
# ============================================================================

def process_year(year: int, extractor: ExtractItems) -> Dict[str, Any]:
    """
    Process all files for a given year.
    
    Returns a dictionary with processing statistics.
    """
    print(f"\n{'='*70}")
    print(f" PROCESSING YEAR: {year}")
    print(f"{'='*70}\n")
    
    # Check if raw files directory exists
    raw_year_dir = os.path.join(RAW_FILINGS_DIR, str(year))
    if not os.path.exists(raw_year_dir):
        print(f"ERROR: Raw files directory not found: {raw_year_dir}")
        return {'status': 'skipped', 'reason': 'directory_not_found'}
    
    # Count files
    raw_files = [f for f in os.listdir(raw_year_dir) 
                 if f.endswith(('.htm', '.html', '.txt'))]
    num_raw_files = len(raw_files)
    
    if num_raw_files == 0:
        print(f"WARNING: No raw files found in {raw_year_dir}")
        return {'status': 'skipped', 'reason': 'no_files'}
    
    print(f"Found {num_raw_files:,} raw files")
    
    # Create output directory
    extracted_year_dir = os.path.join(EXTRACTED_DIR, str(year))
    os.makedirs(extracted_year_dir, exist_ok=True)
    
    # Count already extracted files
    num_extracted = count_extracted_files(year)
    print(f"Already extracted: {num_extracted:,} files")
    
    if num_extracted > 0 and SKIP_EXTRACTED:
        print(f"INFO: Will skip already-extracted files")
    
    # Process files
    print(f"\nStarting extraction...\n")
    start_time = time.time()
    
    extracted_count = 0
    skipped_count = 0
    error_count = 0
    
    from tqdm import tqdm
    
    for filename in tqdm(raw_files, desc=f"Extracting {year}"):
        # Parse filename
        file_info = parse_filename(filename)
        if not file_info:
            error_count += 1
            continue
        
        # Check if already extracted
        json_filename = os.path.splitext(filename)[0] + '.json'
        output_path = os.path.join(extracted_year_dir, json_filename)
        
        if SKIP_EXTRACTED and os.path.exists(output_path):
            skipped_count += 1
            continue
        
        # Extract items
        raw_file_path = os.path.join(raw_year_dir, filename)
        extracted_data = extract_items_from_file(extractor, raw_file_path, file_info)
        
        if extracted_data:
            # Save to JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=2, ensure_ascii=False)
            extracted_count += 1
        else:
            error_count += 1
    
    elapsed = time.time() - start_time
    
    # Print summary
    print(f"\nSUCCESS: Extraction complete for {year}!")
    print(f"   Time elapsed: {elapsed/60:.1f} minutes")
    print(f"   Extracted: {extracted_count:,} files")
    print(f"   Skipped (already done): {skipped_count:,} files")
    if error_count > 0:
        print(f"   Errors: {error_count:,} files")
    
    # Get statistics
    stats = get_extraction_stats(year)
    print(f"\nStatistics:")
    print(f"   Total extracted files: {stats['total_files']:,}")
    print(f"   With Item 1: {stats['has_item_1']:,}")
    print(f"   With Item 1A: {stats['has_item_1a']:,}")
    print(f"   With Item 7: {stats['has_item_7']:,}")
    print(f"   With ALL three items: {stats['has_all_three']:,}")
    
    return {
        'status': 'completed',
        'year': year,
        'extracted': extracted_count,
        'skipped': skipped_count,
        'errors': error_count,
        'elapsed_minutes': elapsed / 60,
        'stats': stats
    }


# ============================================================================
# MAIN SCRIPT
# ============================================================================

def main():
    """Main function to run year-by-year extraction."""
    
    print("="*70)
    print(" YEAR-BY-YEAR 10-K EXTRACTION")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"   Raw files directory: {RAW_FILINGS_DIR}")
    print(f"   Extracted files directory: {EXTRACTED_DIR}")
    print(f"   Items to extract: {', '.join(ITEMS_TO_EXTRACT)}")
    print(f"   Remove tables: {REMOVE_TABLES}")
    print(f"   Skip extracted files: {SKIP_EXTRACTED}")
    print(f"   Year range: {YEAR_START} -> {YEAR_END + 1}")
    print(f"\n{'='*70}\n")
    
    # Verify directories exist
    if not os.path.exists(RAW_FILINGS_DIR):
        print(f"ERROR: Raw filings directory not found: {RAW_FILINGS_DIR}")
        print("   Please update RAW_FILINGS_DIR in the script.")
        return
    
    # Create extracted directory if it doesn't exist
    os.makedirs(EXTRACTED_DIR, exist_ok=True)
    
    # Initialize extractor
    print("Initializing ExtractItems...")
    try:
        # We need to provide dummy paths for initialization
        # ExtractItems will use the actual file paths when we call extract_items()
        extractor = ExtractItems(
            remove_tables=REMOVE_TABLES,
            items_to_extract=ITEMS_TO_EXTRACT,
            include_signature=False,
            raw_files_folder=RAW_FILINGS_DIR,  # Base directory
            extracted_files_folder=EXTRACTED_DIR,  # Base directory
            skip_extracted_filings=SKIP_EXTRACTED,
            special_items_config={'enabled': False}
        )
        
        # Set items_list for 10-K
        extractor.items_list = item_list_10k
        
        print("SUCCESS: ExtractItems initialized successfully\n")
    except Exception as e:
        print(f"ERROR: Failed to initialize ExtractItems: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Process years (newest to oldest)
    years_to_process = list(range(YEAR_START, YEAR_END, -1))
    processing_summary = []
    
    for idx, year in enumerate(years_to_process):
        result = process_year(year, extractor)
        processing_summary.append(result)
        
        # Confirm before next year (if enabled)
        if CONFIRM_BEFORE_NEXT_YEAR and idx < len(years_to_process) - 1:
            next_year = years_to_process[idx + 1]
            response = input(f"\nContinue to {next_year}? (yes/no): ")
            if response.lower() != 'yes':
                print(f"\nStopping. You can resume later by re-running this script.")
                break
        
        print(f"\nSUCCESS: Year {year} processing complete!\n")
    
    # Print final summary
    print(f"\n{'='*70}")
    print(" PROCESSING SUMMARY")
    print(f"{'='*70}\n")
    
    for entry in processing_summary:
        year = entry.get('year', 'Unknown')
        status = entry.get('status', 'unknown')
        
        if status == 'completed':
            print(f"SUCCESS: {year}: {entry.get('extracted', 0):,} files extracted "
                  f"({entry.get('elapsed_minutes', 0):.1f} min)")
        elif status == 'skipped':
            print(f"SKIPPED: {year}: Skipped - {entry.get('reason', 'unknown')}")
        else:
            print(f"ERROR: {year}: {status}")
    
    print(f"\n{'='*70}")
    print("SUCCESS: All processing complete!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
