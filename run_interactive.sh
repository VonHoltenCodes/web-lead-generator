#!/bin/bash

# Interactive scraper for custom locations

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Web Lead Generator - Interactive Restaurant Scraper${NC}"
echo "===================================================="
echo ""

cd scraper
python3 restaurant_lead_finder.py