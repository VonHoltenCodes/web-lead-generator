#!/usr/bin/env python3
"""Interactive Google Business Profile Scraper - General Business Edition"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from general_business_scraper import GoogleBusinessScraperV2
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_user_input():
    """Get location from user"""
    print("\n" + "="*60)
    print("Google Business Profile Scraper - General Business Edition")
    print("="*60)
    print("\nThis scraper finds businesses without websites.")
    print("Searches for general 'business' term in any location.")
    print("You can search by city/state or ZIP code.\n")
    
    # Get location
    while True:
        location = input("Enter location (e.g., 'Chicago, IL' or '60601'): ").strip()
        if location:
            break
        print("Location cannot be empty. Please try again.")
    
    # Ask about mode
    print("\nScraping modes:")
    print("1. Quick test (fewer results, faster)")
    print("2. Full scan (all results, slower)")
    print("3. Debug mode (visible browser)")
    
    mode_choice = input("\nSelect mode (1-3) [default: 1]: ").strip()
    
    mode_map = {
        '1': 'test',
        '2': 'full',
        '3': 'debug',
        '': 'test'
    }
    
    mode = mode_map.get(mode_choice, 'test')
    
    # Fixed category for general businesses
    category = "business"
    
    return location, category, mode


async def run_interactive_scrape():
    """Run scraper with user input"""
    location, category, mode = get_user_input()
    
    print(f"\nStarting {mode} scrape for businesses in '{location}'...")
    print("="*60)
    
    scraper = GoogleBusinessScraperV2(mode=mode)
    
    # Override the locations and categories with user input
    await scraper.run_scrape(
        locations=[location],
        categories=[category]
    )
    
    scraper.print_summary()
    
    # Ask if user wants to export
    print("\n" + "="*60)
    export = input("Export businesses without websites to CSV? (Y/n): ").strip().lower()
    
    if export != 'n':
        import subprocess
        import getpass
        
        # Run export script
        result = subprocess.run(
            ['../../export_leads.sh'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("Export completed successfully!")
        else:
            print(f"Export failed: {result.stderr}")


def main():
    """Main entry point"""
    try:
        asyncio.run(run_interactive_scrape())
    except KeyboardInterrupt:
        print("\n\nScraping cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()