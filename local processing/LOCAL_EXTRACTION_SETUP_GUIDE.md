# Local Extraction Setup Guide

This guide explains how to set up your local machine for year-by-year 10-K extraction.

---

## Two Download Methods

You can choose between **rclone** (automated) or **manual download** (simpler).

---

## Method 1: Manual Download (RECOMMENDED FOR BEGINNERS)

**Pros:**
- ✅ Simple, no setup required
- ✅ No API limits to worry about
- ✅ Full control over what you download
- ✅ Works on any platform

**Cons:**
- ⏱️ Manual step for each year
- 🖱️ Requires browser interaction

### Steps:

1. **Open Google Drive** in your browser
2. **Navigate to:** `My Drive/EDGAR_Project/edgar_crawler/datasets/RAW_FILINGS/10-K/`
3. **For each year:**
   - Right-click on year folder (e.g., `2025`)
   - Select "Download"
   - Wait for download to complete (will be a ZIP file)
   - Extract ZIP to: `~/edgar-crawler/datasets/RAW_FILINGS/10-K/2025/`
4. **Run the notebook** - it will detect the files and start extraction

### Time Estimate:
- Download per year: 5-15 minutes (depending on file count and internet speed)
- Extraction per year: 30-90 minutes

---

## Method 2: rclone (AUTOMATED)

**Pros:**
- ✅ Automated - no manual clicking
- ✅ Can resume interrupted downloads
- ✅ Efficient transfer with chunking
- ✅ Built-in retry logic

**Cons:**
- ⚙️ One-time setup required
- 📚 More complex for beginners
- ⚠️ Possible (but unlikely) API rate limits

### Installation:

#### macOS:
```bash
brew install rclone
```

#### Linux:
```bash
# Ubuntu/Debian
sudo apt install rclone

# Or universal installer
curl https://rclone.org/install.sh | sudo bash
```

#### Windows:
1. Download from: https://rclone.org/downloads/
2. Extract to `C:\rclone\`
3. Add to PATH: System Properties → Environment Variables → Path → Add `C:\rclone\`

### Configuration:

1. **Run configuration wizard:**
   ```bash
   rclone config
   ```

2. **Create new remote:**
   - Choose: `n` (New remote)
   - Name: `gdrive`
   - Storage: Choose number for "Google Drive" (usually `17` or similar)
   - Client ID: Press Enter (use default)
   - Client Secret: Press Enter (use default)
   - Scope: Choose `1` (Full access)
   - Root folder: Press Enter (leave blank)
   - Service Account: Press Enter (no)
   - Auto config: `y` (yes)
   - Browser will open for Google authentication
   - Log in with your Google account
   - Grant permissions
   - Configure as Shared Drive: `n` (no)
   - Confirm: `y` (yes)
   - Quit: `q`

3. **Test configuration:**
   ```bash
   rclone lsd gdrive:
   ```
   Should list your Google Drive folders

4. **Update notebook configuration:**
   - Open `Local_Full_Extraction_Year_by_Year.ipynb`
   - In Configuration section, set:
     ```python
     DOWNLOAD_METHOD = "rclone"
     GDRIVE_RAW_FILINGS_PATH = "gdrive:EDGAR_Project/edgar_crawler/datasets/RAW_FILINGS/10-K"
     ```

### About API Limits:

**Google Drive API Quotas:**
- Free tier: 1 billion queries/day
- User limit: 1000 requests per 100 seconds
- Downloads: Throttled but rarely blocked for personal use

**For year-by-year downloads (3,000-6,000 files per year):**
- ✅ **Will NOT hit limits** under normal circumstances
- Each file = ~1-2 API calls
- Total per year: ~6,000-12,000 calls (well within limits)

**If you DO hit limits:**
rclone automatically handles this with retry logic. You can also:
```bash
# Slow down requests (10 transactions per second)
rclone copy gdrive:path/to/folder /local/path --tpslimit 10 --progress

# Use larger chunks for fewer API calls
rclone copy gdrive:path/to/folder /local/path --drive-chunk-size 128M --progress
```

**To resume interrupted download:**
Just run the same command again - rclone will skip already-downloaded files.

### Manual rclone Command (Alternative to Notebook):

If you prefer command-line instead of notebook automation:

```bash
# Download one year
rclone copy \
  gdrive:EDGAR_Project/edgar_crawler/datasets/RAW_FILINGS/10-K/2025 \
  ~/edgar-crawler/datasets/RAW_FILINGS/10-K/2025 \
  --progress \
  --transfers 4 \
  --drive-chunk-size 128M

# Then run extraction in notebook
```

---

## Recommended Workflow

**For Most Users: Manual Download**
1. Download 2025 folder from Google Drive (browser)
2. Run notebook extraction for 2025
3. Review results
4. Download 2024, extract, repeat...

**For Power Users: rclone**
1. Set up rclone once
2. Let notebook automatically download each year
3. Semi-automated workflow

---

## Disk Space Planning

### Estimated Space Needed Per Year:

| Year | Raw Files | Extracted JSONs | Total   |
|------|-----------|-----------------|---------|
| 2025 | ~1-2 GB   | ~2-4 GB         | ~3-6 GB |
| 2024 | ~4-5 GB   | ~6-8 GB         | ~10-13 GB |
| 2023 | ~4-5 GB   | ~6-8 GB         | ~10-13 GB |
| ...  | ...       | ...             | ...     |

### Workflow for Limited Disk Space:

1. **Process 3-4 recent years** (2025, 2024, 2023, 2022)
2. **Transfer to SSD** (~40-50 GB)
3. **Delete from local machine**
4. **Process next batch** (2021, 2020, 2019, 2018)
5. **Repeat**

### Transfer to SSD:

```bash
# Create SSD directories
mkdir -p /path/to/ssd/EDGAR_RAW_10K
mkdir -p /path/to/ssd/EDGAR_EXTRACTED_10K

# Copy files
cp -r ~/edgar-crawler/datasets/RAW_FILINGS/10-K/* /path/to/ssd/EDGAR_RAW_10K/
cp -r ~/edgar-crawler/datasets/EXTRACTED_FILINGS/10-K/* /path/to/ssd/EDGAR_EXTRACTED_10K/

# Verify counts match
find ~/edgar-crawler/datasets/RAW_FILINGS/10-K -type f | wc -l
find /path/to/ssd/EDGAR_RAW_10K -type f | wc -l

# If counts match, safe to delete local copies
rm -rf ~/edgar-crawler/datasets/RAW_FILINGS/10-K/*
rm -rf ~/edgar-crawler/datasets/EXTRACTED_FILINGS/10-K/*
```

---

## Troubleshooting

### Issue: rclone not found after installation
**Solution:**
```bash
# Find rclone location
which rclone

# Add to PATH in ~/.bashrc or ~/.zshrc
export PATH=$PATH:/path/to/rclone
```

### Issue: Google Drive quota exceeded
**Solution:**
- Wait 24 hours for quota to reset
- Use `--tpslimit 10` to slow down requests
- Switch to manual download for that year

### Issue: Download interrupted
**Solution:**
- For rclone: Re-run same command (will resume)
- For manual: Re-download (Google Drive handles resume automatically)

### Issue: Extraction fails with "file not found"
**Solution:**
- Verify files are in correct directory
- Check year folder structure matches: `RAW_FILINGS/10-K/2025/`
- Ensure files are extracted from ZIP (if downloaded manually)

---

## Next Steps

1. Choose your download method (manual or rclone)
2. If rclone: Complete setup above
3. Open `Local_Full_Extraction_Year_by_Year.ipynb`
4. Update configuration section
5. Start with 2025 (smallest year, good for testing)

---

**Questions?**
- Check the main README.md for project documentation
- See notebook comments for detailed explanations
