#!/bin/bash

# Export businesses without websites to CSV

# Set default output file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="leads_without_websites_${TIMESTAMP}.csv"

# Check if city filter is provided
if [ "$1" ]; then
    CITY_FILTER=" AND city = '$1'"
    OUTPUT_FILE="leads_without_websites_${1,,}_${TIMESTAMP}.csv"
else
    CITY_FILTER=""
fi

# Check if custom output filename is provided
if [ "$2" ]; then
    OUTPUT_FILE="$2"
fi

echo "Exporting businesses without websites..."

# Export to CSV using psql (via tmp to avoid permission issues)
TEMP_FILE="/tmp/${OUTPUT_FILE}"
sudo -u postgres psql -d web_lead_generator -c "\copy (SELECT name, phone, address, city, category, TO_CHAR(last_scraped, 'YYYY-MM-DD HH24:MI:SS') as last_scraped FROM businesses WHERE has_website = false${CITY_FILTER} ORDER BY last_scraped DESC, name) TO '${TEMP_FILE}' WITH CSV HEADER"

# Check if export was successful
if [ $? -eq 0 ]; then
    # Move file to current directory and fix permissions
    sudo mv "$TEMP_FILE" "$OUTPUT_FILE"
    sudo chown $USER:$USER "$OUTPUT_FILE"
    
    # Count the records
    RECORD_COUNT=$(($(wc -l < "$OUTPUT_FILE") - 1))
    echo "Exported $RECORD_COUNT businesses without websites to $OUTPUT_FILE"
else
    echo "Error exporting businesses"
    exit 1
fi