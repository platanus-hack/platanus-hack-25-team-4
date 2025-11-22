-- Initialize database extensions for Active Circles
-- This script runs automatically when the PostgreSQL container starts

-- Enable pgvector extension for vector embeddings
-- Used for AI-powered features like semantic search and profile matching
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable PostGIS extension for geospatial data
-- Used for location-based features and geographic queries
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable pg_trgm for trigram-based text search
-- Used for fuzzy text matching and search optimization
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable uuid-ossp for UUID generation
-- Used for generating unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verify extensions are installed
SELECT
    extname AS "Extension",
    extversion AS "Version"
FROM pg_extension
WHERE extname IN ('vector', 'postgis', 'pg_trgm', 'uuid-ossp')
ORDER BY extname;
