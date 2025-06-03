-- Database schema for Web Lead Generator

-- Create database (run as superuser)
-- CREATE DATABASE web_lead_generator;

-- Business table
CREATE TABLE IF NOT EXISTS businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2) DEFAULT 'IL',
    zip_code VARCHAR(10),
    category VARCHAR(100),
    gbp_url TEXT UNIQUE,
    has_website BOOLEAN DEFAULT FALSE,
    website_url TEXT,
    google_rating DECIMAL(2,1),
    review_count INTEGER,
    last_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Call outcomes enum
CREATE TYPE call_outcome AS ENUM (
    'interested',
    'not_interested', 
    'no_answer',
    'wrong_number',
    'callback',
    'voicemail',
    'already_has_website'
);

-- Call logs table
CREATE TABLE IF NOT EXISTS call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    call_date DATE NOT NULL,
    call_time TIME NOT NULL,
    outcome call_outcome NOT NULL,
    notes TEXT,
    follow_up_date DATE,
    caller_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scrape runs table
CREATE TABLE IF NOT EXISTS scrape_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    location VARCHAR(100),
    category VARCHAR(100),
    businesses_found INTEGER DEFAULT 0,
    businesses_without_websites INTEGER DEFAULT 0,
    new_businesses_added INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'running',
    error_log TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_businesses_has_website ON businesses(has_website);
CREATE INDEX idx_businesses_city ON businesses(city);
CREATE INDEX idx_businesses_category ON businesses(category);
CREATE INDEX idx_call_logs_business_id ON call_logs(business_id);
CREATE INDEX idx_call_logs_outcome ON call_logs(outcome);
CREATE INDEX idx_call_logs_follow_up ON call_logs(follow_up_date);

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_businesses_updated_at BEFORE UPDATE ON businesses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();