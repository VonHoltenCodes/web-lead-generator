# Setup Instructions

## Prerequisites
- Python 3.8+
- PostgreSQL 13+
- Node.js 18+ (for frontend)

## Database Setup

1. Install PostgreSQL if not already installed:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql
```

2. Create database and user:
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE web_lead_generator;
CREATE USER scraper_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE web_lead_generator TO scraper_user;
\q
```

3. Run the schema:
```bash
psql -U scraper_user -d web_lead_generator -f database/schema.sql
```

## Scraper Setup

1. Install dependencies globally (safe dev system):
```bash
sudo pip3 install --break-system-packages -r requirements.txt
```

2. Or install individually:
```bash
pip3 install --break-system-packages playwright psycopg2-binary sqlalchemy python-dotenv
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

4. Create .env file:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

## Running the Scraper

### Test Mode (Limited scraping)
```bash
cd scraper
python google_scraper.py
```

### Full Scrape
Edit the main() function in google_scraper.py to use all locations and categories.

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check PostgreSQL is running: `sudo systemctl status postgresql`
   - Verify credentials in .env file
   - Ensure database exists

2. **Playwright errors**
   - Run: `playwright install-deps`
   - Try with headless=False to debug

3. **No results found**
   - Google may have changed their HTML structure
   - Check selectors in extract_businesses() method
   - Try manual search to verify businesses exist

## Next Steps

1. Set up the API backend
2. Create the Next.js frontend
3. Implement call tracking features
4. Add data export functionality