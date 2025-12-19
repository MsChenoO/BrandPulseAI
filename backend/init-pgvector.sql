-- Phase 4: Initialize pgvector extension
-- This script runs automatically when PostgreSQL container starts

-- Create pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
SELECT * FROM pg_extension WHERE extname = 'vector';
