#!/usr/bin/env python3
"""Export businesses without websites to CSV"""
import csv
import sys
import psycopg2
from datetime import datetime
import argparse

# Database connection
import os
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost/web_lead_generator"
)

def export_businesses_without_websites(city=None, output_file=None):
    """Export businesses without websites to CSV"""
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Build query
        query = """
            SELECT name, phone, address, city, category, last_scraped
            FROM businesses
            WHERE has_website = false
        """
        params = []
        
        if city:
            query += " AND city = %s"
            params.append(city)
            
        query += " ORDER BY last_scraped DESC, name"
        
        # Execute query
        cursor.execute(query, params)
        businesses = cursor.fetchall()
        
        # Generate filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            city_suffix = f"_{city.lower()}" if city else "_all"
            output_file = f"leads_without_websites{city_suffix}_{timestamp}.csv"
        
        # Write to CSV
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Business Name', 'Phone', 'Address', 'City', 'Category', 'Last Scraped'])
            writer.writerows(businesses)
        
        print(f"Exported {len(businesses)} businesses without websites to {output_file}")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return output_file
        
    except Exception as e:
        print(f"Error exporting businesses: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Export businesses without websites to CSV')
    parser.add_argument('--city', help='Filter by city (e.g., Shorewood)')
    parser.add_argument('--output', help='Output filename (default: auto-generated)')
    
    args = parser.parse_args()
    
    export_businesses_without_websites(args.city, args.output)

if __name__ == "__main__":
    main()