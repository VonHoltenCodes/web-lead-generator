"""Google Business Profile scraper with polite delays and multiple modes"""
import asyncio
import random
import json
import re
from datetime import datetime
from urllib.parse import quote
import logging
import sys

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import RealDictCursor

from config import (
    SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX, SESSION_BREAK_MIN, SESSION_BREAK_MAX,
    REQUESTS_PER_SESSION, MAX_RETRIES, TIMEOUT, HEADLESS, VIEWPORT, 
    USER_AGENTS, DATABASE_URL, LOCATIONS, CATEGORIES, SCRAPE_MODES
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GoogleBusinessScraper:
    def __init__(self, mode='test'):
        self.mode = mode
        self.mode_config = SCRAPE_MODES.get(mode, SCRAPE_MODES['test'])
        self.browser = None
        self.context = None
        self.page = None
        self.db_conn = None
        self.businesses_found = 0
        self.businesses_without_websites = 0
        self.new_businesses_added = 0
        self.request_count = 0
        self.session_start_time = datetime.now()
        
    async def init_browser(self):
        """Initialize Playwright browser with anti-detection measures"""
        playwright = await async_playwright().start()
        
        # Use debug mode headless setting if available
        headless = self.mode_config.get('headless', HEADLESS)
        
        logger.info(f"Starting browser in {'headless' if headless else 'visible'} mode")
        
        # Launch browser with stealth settings
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )
        
        # Create context with random user agent
        user_agent = random.choice(USER_AGENTS)
        self.context = await self.browser.new_context(
            viewport=VIEWPORT,
            user_agent=user_agent,
            locale='en-US',
            timezone_id='America/Chicago',
        )
        
        # Add stealth scripts
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        self.page = await self.context.new_page()
        
    def init_database(self):
        """Initialize database connection"""
        self.db_conn = psycopg2.connect(DATABASE_URL)
        logger.info("Database connection established")
        
    async def polite_delay(self):
        """Implement polite delay between requests"""
        delay = random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX)
        logger.info(f"Waiting {delay:.1f} seconds before next request...")
        await asyncio.sleep(delay)
        
    async def session_break(self):
        """Take a longer break between sessions"""
        break_time = random.uniform(SESSION_BREAK_MIN, SESSION_BREAK_MAX)
        logger.info(f"Taking a session break for {break_time:.0f} seconds...")
        logger.info(f"Requests in this session: {self.request_count}")
        await asyncio.sleep(break_time)
        self.request_count = 0
        self.session_start_time = datetime.now()
        
    async def check_session_break(self):
        """Check if we need a session break"""
        self.request_count += 1
        if self.request_count >= REQUESTS_PER_SESSION:
            await self.session_break()
            
    async def search_businesses(self, location, category):
        """Search for businesses in a specific location and category"""
        search_query = f"{category} near {location}"
        search_url = f"https://www.google.com/search?q={quote(search_query)}&tbm=lcl"
        
        logger.info(f"Searching: {search_query}")
        
        try:
            await self.check_session_break()
            await self.page.goto(search_url, wait_until='networkidle', timeout=TIMEOUT)
            await self.polite_delay()
            
            # Wait for results to load - adjusted selector
            try:
                await self.page.wait_for_selector('.rllt__details', timeout=10000)
            except:
                logger.warning(f"No results found for {search_query}")
                return []
            
            all_businesses = []
            page_count = 0
            max_pages = self.mode_config.get('max_pages', 1)
            
            # Get businesses from first page
            businesses = await self.extract_businesses_from_page()
            all_businesses.extend(businesses)
            page_count += 1
            
            # Check for more pages if not at limit
            while page_count < max_pages and await self.has_next_page():
                logger.info(f"Moving to page {page_count + 1} for {search_query}")
                await self.click_next_page()
                await self.polite_delay()
                
                more_businesses = await self.extract_businesses_from_page()
                all_businesses.extend(more_businesses)
                page_count += 1
                
            logger.info(f"Found {len(all_businesses)} businesses for {search_query}")
            return all_businesses
            
        except PlaywrightTimeout:
            logger.error(f"Timeout searching for {search_query}")
            return []
        except Exception as e:
            logger.error(f"Error searching for {search_query}: {str(e)}")
            return []
    
    async def extract_businesses_from_page(self):
        """Extract business information from current page"""
        businesses = []
        
        # Wait a bit for dynamic content to load
        await asyncio.sleep(1)
        
        # Get all business listings - try different selectors
        business_elements = await self.page.query_selector_all('.rllt__details')
        
        # If no results with that selector, try alternatives
        if not business_elements:
            business_elements = await self.page.query_selector_all('[data-hveid]')
        
        for element in business_elements:
            try:
                business = {}
                
                # Extract name
                name_elem = await element.query_selector('.OSrXXb')
                business['name'] = await name_elem.inner_text() if name_elem else None
                
                # Extract phone - look for phone number in various places
                phone = None
                
                # Method 1: Look for phone in the business card details
                details_text = await element.inner_text()
                
                # Log the full text to see what we're getting
                if business['name'] and 'Bedrocks' in business['name']:
                    logger.info(f"Full text for {business['name']}: {details_text[:200]}...")
                
                # Phone number patterns
                phone_patterns = [
                    r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890 or 123-456-7890
                    r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',  # 123-456-7890
                    r'\d{10}'  # 1234567890
                ]
                
                for pattern in phone_patterns:
                    match = re.search(pattern, details_text)
                    if match:
                        phone = match.group()
                        # Clean up the phone number
                        phone = re.sub(r'[^\d\-() ]', '', phone).strip()
                        break
                
                # Method 2: If no phone found, try specific selectors
                if not phone:
                    phone_selectors = ['.LrzXr', '.rllt__details span', 'span[style*="direction:ltr"]']
                    for selector in phone_selectors:
                        phone_elem = await element.query_selector(selector)
                        if phone_elem:
                            text = await phone_elem.inner_text()
                            # Check if it looks like a phone number
                            if re.search(r'\d{3}.*\d{3}.*\d{4}', text):
                                phone = text.strip()
                                break
                
                business['phone'] = phone
                
                # Extract address
                address_elem = await element.query_selector('.rllt__details > div:nth-child(3)')
                business['address'] = await address_elem.inner_text() if address_elem else None
                
                # Extract rating
                rating_elem = await element.query_selector('.yi40Hd')
                if rating_elem:
                    rating_text = await rating_elem.get_attribute('aria-label')
                    if rating_text:
                        try:
                            rating = float(rating_text.split()[0])
                            business['rating'] = rating
                        except:
                            business['rating'] = None
                else:
                    business['rating'] = None
                
                # Get parent link for GBP URL - try different selectors
                gbp_url = None
                website_url = None
                
                # Try to find the parent link
                parent = await element.evaluate_handle('(el) => el.closest("a")')
                if parent:
                    gbp_url = await parent.get_property('href')
                    if gbp_url:
                        gbp_url = await gbp_url.json_value()
                        
                    # Check for website in data attributes
                    data_url = await parent.get_property('dataset')
                    if data_url:
                        data_url_obj = await data_url.json_value()
                        website_url = data_url_obj.get('url', None)
                
                business['gbp_url'] = gbp_url if gbp_url else None
                business['has_website'] = bool(website_url)
                business['website_url'] = website_url
                
                if business['name']:
                    businesses.append(business)
                    logger.info(f"Extracted: {business['name']} - Phone: {business.get('phone', 'None')} - Website: {business['has_website']}")
                    
            except Exception as e:
                logger.error(f"Error extracting business: {str(e)}")
                continue
                
        return businesses
    
    async def has_next_page(self):
        """Check if there's a next page of results"""
        next_button = await self.page.query_selector('a#pnnext')
        return next_button is not None
    
    async def click_next_page(self):
        """Click the next page button"""
        await self.check_session_break()
        await self.page.click('a#pnnext')
        await self.page.wait_for_load_state('networkidle')
    
    def save_business(self, business, location, category):
        """Save business to database"""
        logger.info(f"Attempting to save: {business.get('name')} - GBP URL: {business.get('gbp_url')}")
        try:
            with self.db_conn.cursor() as cursor:
                # Check if business already exists by name and city if no gbp_url
                if business.get('gbp_url'):
                    cursor.execute(
                        "SELECT id FROM businesses WHERE gbp_url = %s",
                        (business.get('gbp_url'),)
                    )
                    existing = cursor.fetchone()
                else:
                    # Fallback to name + city for uniqueness
                    cursor.execute(
                        "SELECT id FROM businesses WHERE name = %s AND city = %s",
                        (business.get('name'), location.split(',')[0])
                    )
                    existing = cursor.fetchone()
                    
                if existing:
                    # Update existing business
                    if business.get('gbp_url'):
                        cursor.execute("""
                            UPDATE businesses 
                            SET name = %s, phone = %s, address = %s, 
                                has_website = %s, website_url = %s,
                                google_rating = %s, last_scraped = CURRENT_TIMESTAMP
                            WHERE gbp_url = %s
                        """, (
                            business.get('name'),
                            business.get('phone'),
                            business.get('address'),
                            business.get('has_website', False),
                            business.get('website_url'),
                            business.get('rating'),
                            business.get('gbp_url')
                        ))
                    else:
                        cursor.execute("""
                            UPDATE businesses 
                            SET phone = %s, address = %s, 
                                has_website = %s, website_url = %s,
                                google_rating = %s, last_scraped = CURRENT_TIMESTAMP
                            WHERE name = %s AND city = %s
                        """, (
                            business.get('phone'),
                            business.get('address'),
                            business.get('has_website', False),
                            business.get('website_url'),
                            business.get('rating'),
                            business.get('name'),
                            location.split(',')[0]
                        ))
                else:
                    # Insert new business
                    cursor.execute("""
                        INSERT INTO businesses 
                        (name, phone, address, city, category, gbp_url, 
                         has_website, website_url, google_rating)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        business.get('name'),
                        business.get('phone'),
                        business.get('address'),
                        location.split(',')[0],  # Extract city
                        category,
                        business.get('gbp_url'),
                        business.get('has_website', False),
                        business.get('website_url'),
                        business.get('rating')
                    ))
                    self.new_businesses_added += 1
                    logger.info(f"Added new business: {business.get('name')}")
                
                self.db_conn.commit()
                
                if not business.get('has_website', False):
                    self.businesses_without_websites += 1
                    
        except Exception as e:
            logger.error(f"Error saving business {business.get('name')}: {str(e)}")
            self.db_conn.rollback()
                    
    async def run_scrape(self, locations=None, categories=None):
        """Run the scraping process based on mode"""
        await self.init_browser()
        self.init_database()
        
        # Apply mode configurations
        mode_locations = self.mode_config.get('locations')
        mode_categories = self.mode_config.get('categories')
        
        # Use mode limits or provided values
        if mode_locations is not None:
            locations = (locations or LOCATIONS)[:mode_locations]
        else:
            locations = locations or LOCATIONS
            
        if mode_categories is not None:
            categories = (categories or CATEGORIES)[:mode_categories]
        else:
            categories = categories or CATEGORIES
        
        logger.info(f"Starting {self.mode} scrape")
        logger.info(f"Locations: {locations}")
        logger.info(f"Categories: {categories}")
        
        # Create scrape run record
        run_id = self.create_scrape_run()
        
        try:
            for location in locations:
                for category in categories:
                    businesses = await self.search_businesses(location, category)
                    logger.info(f"Processing {len(businesses)} businesses from {location} - {category}")
                    
                    for business in businesses:
                        self.save_business(business, location, category)
                        self.businesses_found += 1
                    
                    # Polite delay between searches
                    await self.polite_delay()
                    
            # Update scrape run with results
            self.update_scrape_run(run_id, 'completed')
            
        except Exception as e:
            logger.error(f"Scraping error: {str(e)}")
            self.update_scrape_run(run_id, 'failed', str(e))
            raise
            
        finally:
            await self.cleanup()
    
    def create_scrape_run(self):
        """Create a new scrape run record"""
        with self.db_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO scrape_runs (start_time, status)
                VALUES (CURRENT_TIMESTAMP, 'running')
                RETURNING id
            """)
            run_id = cursor.fetchone()[0]
            self.db_conn.commit()
            return run_id
    
    def update_scrape_run(self, run_id, status, error_log=None):
        """Update scrape run with results"""
        with self.db_conn.cursor() as cursor:
            cursor.execute("""
                UPDATE scrape_runs
                SET end_time = CURRENT_TIMESTAMP,
                    businesses_found = %s,
                    businesses_without_websites = %s,
                    new_businesses_added = %s,
                    status = %s,
                    error_log = %s
                WHERE id = %s
            """, (
                self.businesses_found,
                self.businesses_without_websites,
                self.new_businesses_added,
                status,
                error_log,
                run_id
            ))
            self.db_conn.commit()
    
    async def cleanup(self):
        """Clean up resources"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.db_conn:
            self.db_conn.close()
            
    def print_summary(self):
        """Print scraping summary"""
        logger.info("=" * 50)
        logger.info(f"Scraping Summary ({self.mode} mode)")
        logger.info("=" * 50)
        logger.info(f"Total businesses found: {self.businesses_found}")
        logger.info(f"New businesses added: {self.new_businesses_added}")
        logger.info(f"Businesses without websites: {self.businesses_without_websites}")
        logger.info("=" * 50)


async def test_scrape():
    """Quick test scrape with minimal data"""
    logger.info("Running TEST scrape - 1 location, 2 categories, 1 page max")
    scraper = GoogleBusinessScraper(mode='test')
    await scraper.run_scrape()
    scraper.print_summary()


async def full_scrape():
    """Full production scrape"""
    logger.info("Running FULL scrape - All locations and categories")
    scraper = GoogleBusinessScraper(mode='full')
    await scraper.run_scrape()
    scraper.print_summary()


async def debug_scrape():
    """Debug scrape with visible browser"""
    logger.info("Running DEBUG scrape - Browser will be visible")
    scraper = GoogleBusinessScraper(mode='debug')
    await scraper.run_scrape()
    scraper.print_summary()


def main():
    """Main entry point with mode selection"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Google Business Profile Scraper')
    parser.add_argument(
        'mode',
        choices=['test', 'full', 'debug'],
        help='Scraping mode to run'
    )
    
    args = parser.parse_args()
    
    # Run the appropriate scraping function
    if args.mode == 'test':
        asyncio.run(test_scrape())
    elif args.mode == 'full':
        asyncio.run(full_scrape())
    elif args.mode == 'debug':
        asyncio.run(debug_scrape())


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments provided, default to test mode
        logger.info("No mode specified, running in test mode")
        asyncio.run(test_scrape())
    else:
        main()