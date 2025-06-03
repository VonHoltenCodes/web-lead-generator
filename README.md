# Web Lead Generator

A system to identify local businesses without websites and manage outreach campaigns.

## Overview

This tool scrapes Google Business Profiles to find businesses without websites, stores their contact information, and provides an interface for managing outreach calls.

## Current Status

✅ **Completed:**
- Database schema designed and implemented (PostgreSQL)
- Two scraper versions:
  - V1: Basic scraper (limited phone extraction)
  - V2: Click-for-details scraper (successful phone extraction)
- Phone number extraction working reliably in V2
- Three scraping modes: test, full, debug
- Polite scraping with anti-detection measures
- Respects server resources (3-5 sec delays, 2-3 min breaks)
- Industry-specific scrapers (restaurant and general business)
- Pagination support (up to 5 pages/100 results)
- Memory management via browser restarts every 50 businesses
- **NEW: Incremental saving to prevent data loss on timeouts**

🚧 **Known Issues (Fixed):**
- ~~Timeout causing complete data loss~~ - Fixed with incremental saving
- ~~Memory overflow after ~60 businesses~~ - Fixed with browser restart logic

🚧 **Current Known Issues:**
- General business scraper sometimes shows duplicate phone numbers across businesses
- Some businesses may have incomplete address extraction
- Website detection could be improved for businesses with complex menu structures

📋 **Immediate Next Steps:**
1. Improve phone number deduplication logic
2. Build basic call tracking interface (Next.js)
3. Implement TCPA compliance for B2B calling
4. Add phone number validation
5. Create automated scheduling for regular scrapes

## Target Area

Southwestern Chicago suburbs:
- Shorewood
- Plainfield
- Joliet
- Naperville
- Channahon
- Minooka

## Project Structure

```
web-lead-generator/
├── scraper/                    # Python scraping scripts
│   ├── google_scraper.py      # V1 scraper (no phone extraction)
│   ├── google_scraper_v2.py  # V2 scraper (clicks for details)
│   ├── restaurant_lead_finder.py # Restaurant-specific interactive scraper
│   ├── general_business/      # General business scraper
│   │   ├── general_business_scraper.py
│   │   └── general_business_finder.py
│   └── config.py              # Scraper configuration
├── database/                   # Database schemas
│   └── schema.sql             # PostgreSQL schema
├── api/                       # Backend API (pending)
├── frontend/                  # Next.js interface (pending)
├── run_scraper.sh            # Run V1 scraper
├── run_scraper_v2.sh         # Run V2 scraper (recommended)
└── requirements.txt          # Python dependencies
```

## Quick Start

### Industry-Specific Scrapers

```bash
# Restaurant Lead Finder - Interactive location selection
./run_interactive.sh

# General Business Finder - Searches for any business type
./run_general_business_finder.sh
```

### General Scraping Commands

```bash
# Run test scrape (1 location, 1 category)
./run_scraper_v2.sh test

# Run debug scrape (visible browser)
./run_scraper_v2.sh debug

# Run full scrape (all locations/categories)
./run_scraper_v2.sh full

# Export results to CSV
./export_leads.sh
./export_leads.sh Shorewood  # Filter by city
```

## Features

- **Industry-Specific Scrapers**: Fine-tuned scripts for different business types
  - Restaurant Lead Finder - Optimized for restaurant "Menu" button patterns
  - General Business Finder - Clicks "Website" links to capture actual URLs
- **Interactive Mode**: Choose any location to search
- **Polite Scraping**: 3-5 second delays, 2-3 minute session breaks
- **Phone Extraction**: Successfully extracts phone numbers
- **Anti-Detection**: User agent rotation, stealth mode
- **Progress Tracking**: Database tracks scrape runs and results
- **CSV Export**: Export leads to CSV with city filtering

## License

Private repository - All rights reserved