#!/usr/bin/env python3
"""Check which dependencies are missing in the current environment."""

import sys
from pathlib import Path

# Add repo to path
REPO_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_DIR))

required_packages = {
    'beautifulsoup4': 'bs4',
    'click': 'click',
    'cssutils': 'cssutils',
    'numpy': 'numpy',
    'lxml': 'lxml',
    'pandas': 'pandas',
    'requests': 'requests',
    'tqdm': 'tqdm',
    'pathos': 'pathos'
}

print("Checking dependencies...")
print(f"Python: {sys.executable}\n")

missing = []
for package_name, import_name in required_packages.items():
    try:
        __import__(import_name)
        print(f"OK: {package_name}")
    except ImportError:
        print(f"MISSING: {package_name}")
        missing.append(package_name)

print("\n" + "="*50)

# Try importing ExtractItems
try:
    from extract_items import ExtractItems
    print("SUCCESS: ExtractItems can be imported!")
except Exception as e:
    print(f"FAILED: Cannot import ExtractItems: {e}")

if missing:
    print(f"\nMissing packages: {', '.join(missing)}")
    print("\nTo install missing packages, run:")
    print(f"  conda activate base")
    print(f"  pip install {' '.join(missing)}")
else:
    print("\nAll dependencies are installed!")


