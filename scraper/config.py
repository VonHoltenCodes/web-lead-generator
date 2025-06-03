"""Configuration for the web scraper"""
import os
from dotenv import load_dotenv

load_dotenv()

# Target locations
LOCATIONS = [
    "Shorewood, IL",
    "Plainfield, IL", 
    "Joliet, IL",
    "Naperville, IL",
    "Channahon, IL",
    "Minooka, IL"
]

# Business categories to search
CATEGORIES = [
    "restaurant",
    "plumber",
    "electrician",
    "contractor",
    "landscaping",
    "auto repair",
    "hair salon",
    "dentist",
    "real estate agent",
    "lawyer",
    "accountant",
    "insurance agent"
]

# Scraping settings - Polite delays
SCRAPE_DELAY_MIN = 3  # seconds between requests
SCRAPE_DELAY_MAX = 5  # seconds between requests
SESSION_BREAK_MIN = 120  # seconds (2 minutes) between sessions
SESSION_BREAK_MAX = 180  # seconds (3 minutes) between sessions
REQUESTS_PER_SESSION = 10  # Number of requests before taking a break
MAX_RETRIES = 3
TIMEOUT = 30000  # milliseconds

# Scrape modes
SCRAPE_MODES = {
    'test': {
        'locations': 1,  # Number of locations to scrape
        'categories': 2,  # Number of categories per location
        'max_pages': 1,  # Max result pages per search
        'description': 'Quick test with minimal data'
    },
    'full': {
        'locations': None,  # None means all locations
        'categories': None,  # None means all categories
        'max_pages': 5,  # Max result pages per search
        'description': 'Full production scrape'
    },
    'debug': {
        'locations': 1,
        'categories': 1,
        'max_pages': 2,  # Test pagination in debug mode
        'headless': False,  # Show browser for debugging
        'description': 'Debug mode with visible browser'
    }
}

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost/web_lead_generator"
)

# Browser settings
HEADLESS = True  # Set to False for debugging
VIEWPORT = {"width": 1920, "height": 1080}

# User agents rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]