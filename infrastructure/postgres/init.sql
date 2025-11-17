-- Initialize CreatorSync Database
-- This script runs on first database creation

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create database if not exists (already done by Docker)
-- Additional setup can go here

-- Create indexes for common queries
-- These will be created by Alembic migrations, but keeping for reference

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'CreatorSync database initialized successfully';
END $$;
