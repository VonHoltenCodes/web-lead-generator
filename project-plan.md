# Local Business Scraper & Outreach System - Project Plan

## Project Overview
Build a system to identify local businesses without websites, extract contact info, and manage outreach calls.

## Phase 1: Tech Stack Definition

### Core Technologies
- **Scraper**: Python with Playwright (handles JavaScript-heavy Google Business Profile pages)
- **Database**: PostgreSQL (better JSON support for varied business data)
- **Call Tracking Interface**: Next.js with TypeScript
- **Backend API**: FastAPI (Python) or Express (Node.js)
- **Queue System**: Redis + Celery (for scraping jobs)

### Required Libraries/Tools
```
- playwright / puppeteer-extra (with stealth plugin)
- BeautifulSoup4 / lxml (HTML parsing)
- psycopg2 (PostgreSQL adapter)
- pandas (data manipulation)
- Next.js + Tailwind CSS (UI)
- react-table or AG-Grid (data display)
```

## Phase 2: Database Schema

### Tables Needed
1. **businesses**
   - id (UUID)
   - name
   - phone
   - address
   - category
   - gbp_url
   - has_website (boolean)
   - website_url (nullable)
   - last_scraped (timestamp)
   - scrape_source

2. **call_logs**
   - id
   - business_id (FK)
   - call_date
   - call_time
   - outcome (enum: interested, not_interested, no_answer, wrong_number, callback)
   - notes
   - follow_up_date
   - caller_id

3. **scrape_runs**
   - id
   - start_time
   - end_time
   - businesses_found
   - businesses_without_websites
   - errors_count
   - status

## Phase 3: Scraper Architecture

### Key Components
1. **URL Generator**
   - Creates Google Business Profile search URLs by location + category
   - Example: "restaurants near Joliet, IL"

2. **Anti-Detection Measures**
   - Rotating user agents
   - Random delays (2-5 seconds between requests)
   - Proxy rotation (if needed)
   - Browser fingerprint randomization
   - Session management

3. **Data Extraction Logic**
   ```python
   # Pseudocode
   - Search for businesses in target area
   - For each result:
     - Extract business name, phone, address
     - Check for website field
     - If no website found:
       - Double-check with Google search "{name} {city} website"
       - Save to database with has_website = false
   ```

### Questions to Address:
- How to handle pagination on GBP results?
- What's the rate limit before triggering captchas?
- Should we use residential proxies?
- How to detect and handle blocked requests?

## Phase 4: Call Tracking Interface

### UI Components
1. **Dashboard**
   - Total businesses found
   - Businesses without websites
   - Calls made today/week/month
   - Conversion rate

2. **Call Queue View**
   ```
   | Business Name | Phone | Category | Last Contact | Action |
   |--------------|-------|----------|--------------|---------|
   | Joe's Pizza  | 815-555-0123 | Restaurant | Never | [Call] [Skip] |
   ```

3. **Call Response Form**
   - Quick buttons: Interested / Not Interested / No Answer / Callback
   - Notes field
   - Schedule follow-up
   - Mark as "has website" (for false positives)

4. **Features**
   - Click-to-copy phone number
   - Quick Google search button
   - View business on Google Maps
   - Export today's call list
   - Import call results

## Phase 5: Data Visualization & Export

### Reports Needed
- Businesses by category breakdown
- Geographic heatmap of opportunities
- Best calling times analysis
- Conversion funnel
- CSV export with filters

## Phase 6: Vagueness to Clarify

### Business Logic Questions
1. How recent should the scrape data be? (Daily? Weekly?)
2. Multiple phone numbers - which to prioritize?
3. Franchise detection - skip McDonald's locations?
4. How to handle businesses with Facebook pages but no website?
5. Minimum business age/review count filters?

### Technical Questions
1. Scraper hosting - local machine or cloud?
2. How to handle GBP's dynamic loading?
3. Database backup strategy?
4. User authentication for call interface?

## Phase 7: MVP Definition

### MVP Features (Week 1-2)
1. Basic scraper for one business category
2. PostgreSQL database setup
3. Simple web interface to view businesses without websites
4. Manual CSV export
5. Basic call logging

### Post-MVP Additions
1. Automated scheduling
2. Multi-user support
3. Advanced filtering
4. Call script templates
5. Email integration for follow-ups
6. Performance analytics

## Implementation Timeline

### Week 1
- Set up development environment
- Create database schema
- Build basic scraper prototype
- Test on 10-20 businesses

### Week 2
- Add anti-detection measures
- Build basic Next.js interface
- Implement call logging
- Test with 100+ businesses

### Week 3
- Add data export features
- Implement filtering/search
- Performance optimization
- Full area scraping

### Week 4
- Polish UI
- Add reporting features
- Documentation
- Deployment setup

## Risk Mitigation

1. **Scraping Blocks**: Have multiple Google accounts, use proxies
2. **Data Accuracy**: Cross-reference with other sources
3. **Legal Compliance**: Document business purpose, add opt-out mechanism
4. **False Positives**: Manual verification options in UI

## Current Progress & Next Steps

### ✅ Completed
1. Created project repository
2. Set up PostgreSQL database with full schema
3. Built two scrapers:
   - V1: Basic scraper (searches only, limited data)
   - V2: Click-for-details scraper (gets phone numbers reliably)
4. Implemented polite delays and session management
5. Created three scraping modes (test/debug/full)
6. Successfully extracting phone numbers via V2 scraper
7. Database properly stores business data

### 🚧 Current Issues (As of Last Test)
1. **Website Detection Bug**: All businesses showing same website URL (markson59.com)
   - Menu button clicking might be interfering with detection
   - Need to isolate website URLs per business
2. **Duplicate GBP URLs**: All businesses getting same GBP URL
   - Causing database to only save 1 business per run
   - Need to capture URL before clicking into details
3. **Data Carryover**: Previous business data bleeding into next extraction

### 📋 Immediate Next Steps

1. **Fix V2 Scraper Bugs** (Priority: CRITICAL)
   - Store current URL before extracting details
   - Reset business data between extractions
   - Fix website detection logic
   - Ensure unique GBP URLs per business

2. **Build CSV Export** (Priority: HIGH)
   - Export businesses without websites
   - Include: Name, Phone, Address, Category, City
   - Add date range filters
   - Command line tool first, then web UI

3. **Create Basic Call Interface** (Priority: HIGH)
   - Simple Next.js app
   - List businesses without websites
   - Click-to-copy phone numbers
   - Track call outcomes
   - Add notes per call

4. **Legal Compliance** (Priority: HIGH)
   - Research TCPA regulations for B2B calls
   - Implement do-not-call list checking
   - Add opt-out tracking

5. **Data Validation** (Priority: MEDIUM)
   - Validate phone number formats
   - Remove duplicate businesses
   - Flag suspicious data

### 🎯 MVP Status

**Completed:**
- ✅ Database setup
- ✅ Scraper with phone extraction (V2)
- ✅ Polite scraping implementation

**In Progress:**
- ⏳ Fix website/URL detection bugs
- ⏳ CSV export functionality

**Pending:**
- Basic web interface
- Call tracking features
- Legal compliance checks

**Recent Test Results:**
- 20/20 businesses had phone numbers extracted
- All showed same website (bug)
- Only 1 business saved to DB (duplicate URL bug)