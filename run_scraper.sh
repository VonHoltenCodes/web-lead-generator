#!/bin/bash

# Script to run the Google Business Profile scraper

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Web Lead Generator - Scraper${NC}"
echo "==============================="
echo ""

# Check if mode is provided
if [ $# -eq 0 ]; then
    echo "Usage: ./run_scraper.sh [mode]"
    echo ""
    echo "Available modes:"
    echo "  test  - Quick test with 1 location, 2 categories (default)"
    echo "  full  - Full scrape of all locations and categories"
    echo "  debug - Debug mode with visible browser"
    echo ""
    echo "Example: ./run_scraper.sh test"
    echo ""
    MODE="test"
    echo -e "${YELLOW}No mode specified, using 'test' mode${NC}"
else
    MODE=$1
fi

# Run the scraper
echo -e "${GREEN}Starting scraper in ${MODE} mode...${NC}"
echo ""

cd scraper
python3 google_scraper.py $MODE

echo ""
echo -e "${GREEN}Scraping complete!${NC}"