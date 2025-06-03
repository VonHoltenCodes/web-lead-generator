# Changelog

## 2025-06-03 - Incremental Saving Fix

### Problem
- Restaurant scraper was timing out on page 4 when scraping Joliet, IL
- Found 27 restaurants without websites across 60 total businesses
- But timeout caused "Total businesses found: 0" - all data was lost
- Root cause: Scraper accumulated all results in memory before saving to database

### Solution 
- Modified both V2 scraper and general business scraper to save incrementally
- Now saves each business to database immediately after extraction
- If timeout occurs, partial results are preserved
- Added new `search_businesses_and_save()` method that saves incrementally
- Kept original `search_businesses()` method for backward compatibility
- Changed error handling to mark runs as "partial" instead of "failed" when timeouts occur

### Files Modified
- `/scraper/google_scraper_v2.py`
- `/scraper/general_business/general_business_scraper.py`

### Benefits
- No more data loss on timeouts
- Can handle larger scraping runs without memory issues
- Partial results are saved even if scraper crashes
- Better progress tracking as businesses save in real-time