"""Google Business Profile scraper - General Business Edition
Searches for general 'business' term and clicks Website links to get actual URLs"""
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

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


class GoogleBusinessScraperV2:
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
        """Legacy method that returns all businesses - kept for compatibility"""
        # This is a wrapper that collects results for backward compatibility
        temp_businesses = []
        self._temp_businesses = temp_businesses
        self._original_save = self.save_business
        
        # Override save_business temporarily to collect instead of save
        def collect_business(business, location, category):
            temp_businesses.append(business)
        self.save_business = collect_business
        
        try:
            await self.search_businesses_and_save(location, category)
        finally:
            # Restore original save method
            self.save_business = self._original_save
            del self._temp_businesses
            
        return temp_businesses
    
    async def search_businesses_and_save(self, location, category):
        """Search for businesses and save them incrementally"""
        search_query = f"{category} near {location}"
        search_url = f"https://www.google.com/search?q={quote(search_query)}&tbm=lcl"
        
        logger.info(f"Searching: {search_query}")
        
        try:
            await self.check_session_break()
            await self.page.goto(search_url, wait_until='networkidle', timeout=TIMEOUT)
            await self.polite_delay()
            
            # Wait for results to load
            try:
                await self.page.wait_for_selector('.rllt__details', timeout=10000)
            except:
                logger.warning(f"No results found for {search_query}")
                return
            
            page_count = 0
            max_pages = self.mode_config.get('max_pages', 1)
            
            while page_count < max_pages:
                logger.info(f"Processing page {page_count + 1} of {max_pages}")
                
                # Get list of business links - try multiple selectors
                business_links = await self.page.query_selector_all('a.hfpxzc')
                if not business_links:
                    # Try alternative selectors
                    business_links = await self.page.query_selector_all('a[data-cid]')
                if not business_links:
                    # Try another approach - look for business cards
                    business_links = await self.page.query_selector_all('.VkpGBb > a')
                if not business_links:
                    # Last resort - any link in the results area
                    business_links = await self.page.query_selector_all('.rllt__details')
                    
                logger.info(f"Found {len(business_links)} business elements on page {page_count + 1}")
                
                # Process each business element
                for i in range(min(20, len(business_links))):  # Limit to 20 per page
                    try:
                        # Re-query elements since page might have changed
                        current_elements = await self.page.query_selector_all('.rllt__details')
                        if i >= len(current_elements):
                            break
                            
                        element = current_elements[i]
                        
                        # Get the business name first
                        name_elem = await element.query_selector('.OSrXXb')
                        if not name_elem:
                            name_elem = await element.query_selector('.qBF1Pd')
                        business_name = await name_elem.inner_text() if name_elem else f"Business {i+1}"
                        
                        logger.info(f"Processing business {i+1}/{min(20, len(business_links))}: {business_name}")
                        
                        # Find the clickable link within this element
                        parent_elem = await element.evaluate_handle('(el) => el.closest("a")')
                        if parent_elem:
                            # Click on the business
                            await parent_elem.click()
                            await asyncio.sleep(2)  # Wait for details to load
                        else:
                            # Try clicking the element itself
                            await element.click()
                            await asyncio.sleep(2)
                        
                        # Store the current URL before extracting details
                        current_url = self.page.url
                        
                        # Extract business details from the side panel
                        business = await self.extract_business_details(business_name)
                        
                        if business:
                            # Make sure we have the correct GBP URL
                            business['gbp_url'] = current_url
                            # Save immediately instead of accumulating
                            self.save_business(business, location, category)
                            self.businesses_found += 1
                        
                        # Go back to search results
                        await self.page.go_back()
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error processing business {i+1}: {str(e)}")
                        continue
                
                page_count += 1
                
                # Check if there's a next page and we haven't reached the limit
                if page_count < max_pages and await self.has_next_page():
                    logger.info(f"Moving to page {page_count + 1}")
                    await self.click_next_page()
                    await self.polite_delay()
                else:
                    break
                    
            logger.info(f"Processed businesses for {search_query} across {page_count} pages")
            
        except PlaywrightTimeout:
            logger.error(f"Timeout searching for {search_query} - partial results saved")
            # Don't return, let the partial results stand
        except Exception as e:
            logger.error(f"Error searching for {search_query}: {str(e)} - partial results saved")
            # Don't return, let the partial results stand
    
    async def has_next_page(self):
        """Check if there's a next page of results"""
        next_button = await self.page.query_selector('a#pnnext')
        return next_button is not None
    
    async def click_next_page(self):
        """Click the next page button"""
        await self.check_session_break()
        await self.page.click('a#pnnext')
        await self.page.wait_for_load_state('networkidle')
        # Wait for new results to load
        await asyncio.sleep(2)
    
    async def extract_business_details(self, business_name):
        """Extract business information from the detail panel"""
        try:
            business = {'name': business_name}
            
            # Wait for details panel to load - try multiple selectors
            try:
                await self.page.wait_for_selector('[role="main"]', timeout=5000)
            except:
                # Try alternative selector
                await self.page.wait_for_selector('.xpdopen', timeout=5000)
            
            # Get the entire page content for phone extraction
            page_content = await self.page.content()
            
            # Extract phone number - look for various patterns
            phone_patterns = [
                r'href="tel:([^"]+)"',  # Tel links
                r'(?:Phone:|Call|📞|☎️)\s*:?\s*(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
                r'>\s*(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\s*<',  # Phone in HTML
                r'\b(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})\b'  # Generic phone pattern
            ]
            
            phone = None
            for pattern in phone_patterns:
                match = re.search(pattern, page_content)
                if match:
                    phone = match.group(1).strip()
                    # Clean up phone number
                    phone = re.sub(r'^tel:', '', phone)
                    break
            business['phone'] = phone
            
            # Extract address - look for address patterns
            address_patterns = [
                r'<span[^>]*>([^<]+(?:St|Ave|Rd|Blvd|Dr|Way|Ln|Pkwy)[^<]*)</span>',
                r'>([0-9]+[^<]+(?:St|Ave|Rd|Blvd|Dr|Way|Ln|Pkwy)[^<]*)<',
            ]
            
            address = None
            for pattern in address_patterns:
                match = re.search(pattern, page_content)
                if match:
                    address = match.group(1).strip()
                    break
            business['address'] = address
            
            # Extract rating
            rating_match = re.search(r'(\d+\.?\d*)\s*(?:star|★)', page_content, re.IGNORECASE)
            if rating_match:
                try:
                    business['rating'] = float(rating_match.group(1))
                except:
                    business['rating'] = None
            else:
                business['rating'] = None
            
            # Check for website - just look for presence of website link/button
            website_url = None
            has_website = False
            
            try:
                # Look for website indicators
                website_selectors = [
                    'a[data-tooltip="Open website"]',
                    'a[data-item-id="authority"]',
                    'a:has-text("Website")',
                    'span:has-text("Website")',
                    '[aria-label*="Website"]',
                    'button:has-text("Website")'
                ]
                
                for selector in website_selectors:
                    website_element = await self.page.query_selector(selector)
                    if website_element:
                        has_website = True
                        logger.info(f"Found website indicator for {business_name}")
                        # We don't need to click - just knowing it exists is enough
                        break
                
                if not has_website:
                    logger.info(f"No website found for {business_name}")
                    
            except Exception as e:
                logger.debug(f"Error checking for website: {str(e)}")
                
            business['has_website'] = has_website
            business['website_url'] = website_url  # Will be None since we're not extracting URLs
            
            # GBP URL will be set by the caller
            
            logger.info(f"Extracted: {business['name']} - Phone: {business.get('phone', 'None')} - Website: {business['has_website']}")
            
            return business
            
        except Exception as e:
            logger.error(f"Error extracting business details: {str(e)}")
            return None
    
    def save_business(self, business, location, category):
        """Save business to database"""
        logger.info(f"Attempting to save: {business.get('name')} - Phone: {business.get('phone')} - GBP URL: {business.get('gbp_url')}")
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
                    logger.info(f"Added new business: {business.get('name')} with phone: {business.get('phone')}")
                
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
                    # Pass location and category to search_businesses
                    # so it can save incrementally
                    await self.search_businesses_and_save(location, category)
                    
                    # Polite delay between searches
                    await self.polite_delay()
                    
            # Update scrape run with results
            self.update_scrape_run(run_id, 'completed')
            
        except Exception as e:
            logger.error(f"Scraping error: {str(e)}")
            # Even if we had an error, update with the partial results we got
            self.update_scrape_run(run_id, 'partial', f"Partial results saved. Error: {str(e)}")
            
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
    logger.info("Running TEST scrape V2 - 1 location, 1 category, clicking for details")
    scraper = GoogleBusinessScraperV2(mode='test')
    # Override to just get a few businesses
    scraper.mode_config['categories'] = 1
    await scraper.run_scrape()
    scraper.print_summary()


async def debug_scrape():
    """Debug scrape with visible browser"""
    logger.info("Running DEBUG scrape V2 - Browser will be visible")
    scraper = GoogleBusinessScraperV2(mode='debug')
    await scraper.run_scrape()
    scraper.print_summary()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Google Business Profile Scraper V2')
    parser.add_argument(
        'mode',
        choices=['test', 'debug'],
        help='Scraping mode to run'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'test':
        asyncio.run(test_scrape())
    elif args.mode == 'debug':
        asyncio.run(debug_scrape())


if __name__ == "__main__":
    if len(sys.argv) == 1:
        logger.info("No mode specified, running in test mode")
        asyncio.run(test_scrape())
    else:
        main()