-- Initialize database extensions for Active Circles
-- This script runs automatically when the PostgreSQL container starts

-- Enable pgvector extension for vector embeddings
-- Used for AI-powered features like semantic search and profile matching
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable pg_trgm for trigram-based text search
-- Used for fuzzy text matching and search optimization
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable uuid-ossp for UUID generation
-- Used for generating unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable PostGIS for geospatial queries
-- Used for collision detection and location-based matching
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Verify extensions are installed
SELECT
    extname AS "Extension",
    extversion AS "Version"
FROM pg_extension
WHERE extname IN ('vector', 'pg_trgm', 'uuid-ossp', 'postgis', 'postgis_topology')
ORDER BY extname;
