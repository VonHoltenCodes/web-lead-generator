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

🚧 **Known Issues:**
- Website detection showing same URL for all businesses (markson59.com)
- GBP URLs getting duplicated causing only 1 business to save per run
- Need better unique business tracking

📋 **Immediate Next Steps:**
1. Fix website detection logic in V2 scraper
2. Ensure unique GBP URLs per business
3. Create CSV export functionality
4. Build basic call tracking interface
5. Address legal compliance for calling

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
  - Restaurant Lead Finder (currently available)
- **Interactive Mode**: Choose any location to search
- **Polite Scraping**: 3-5 second delays, 2-3 minute session breaks
- **Phone Extraction**: Successfully extracts phone numbers
- **Anti-Detection**: User agent rotation, stealth mode
- **Progress Tracking**: Database tracks scrape runs and results
- **CSV Export**: Export leads to CSV with city filtering

## License

Private repository - All rights reserved