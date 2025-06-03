#!/bin/bash

# Interactive scraper for general businesses

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Web Lead Generator - General Business Scraper${NC}"
echo "==============================================="
echo ""

cd scraper/general_business
python3 general_business_finder.py