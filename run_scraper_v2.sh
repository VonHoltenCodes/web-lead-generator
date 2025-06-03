#!/bin/bash

# Script to run the Google Business Profile scraper V2 (with click for details)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Web Lead Generator - Scraper V2 (Click for Details)${NC}"
echo "===================================================="
echo ""

# Check if mode is provided
if [ $# -eq 0 ]; then
    echo "Usage: ./run_scraper_v2.sh [mode]"
    echo ""
    echo "Available modes:"
    echo "  test  - Quick test with clicking for phone numbers"
    echo "  debug - Debug mode with visible browser"
    echo ""
    echo "Example: ./run_scraper_v2.sh test"
    echo ""
    MODE="test"
    echo -e "${YELLOW}No mode specified, using 'test' mode${NC}"
else
    MODE=$1
fi

# Run the scraper
echo -e "${GREEN}Starting scraper V2 in ${MODE} mode...${NC}"
echo ""

cd scraper
python3 google_scraper_v2.py $MODE

echo ""
echo -e "${GREEN}Scraping complete!${NC}"