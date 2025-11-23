-- SQL to add spatial indexes for collision detection performance
-- This file should be added to a Prisma migration after running:
-- npx prisma migrate dev --create-only --name add_spatial_indexes

-- Add PostGIS extension if not already present
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create spatial index on User position for collision detection queries
-- This index dramatically improves performance of ST_DWithin and ST_Distance queries
CREATE INDEX IF NOT EXISTS idx_user_position_gist
ON "User" USING GIST (
  ST_MakePoint(COALESCE("centerLon", 0), COALESCE("centerLat", 0))
) WHERE "centerLat" IS NOT NULL AND "centerLon" IS NOT NULL;

-- Create composite index for active circles with user position
-- This optimizes the JOIN query in collision detection
CREATE INDEX IF NOT EXISTS idx_circle_user_active
ON "Circle" ("userId", "status", "expiresAt", "startAt")
WHERE status = 'active';

-- Create index on User centerLat/centerLon for faster filtering
-- This helps when filtering users with valid positions
CREATE INDEX IF NOT EXISTS idx_user_position_not_null
ON "User" ("centerLat", "centerLon")
WHERE "centerLat" IS NOT NULL AND "centerLon" IS NOT NULL;

-- Verify indexes were created
SELECT
  schemaname,
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE tablename IN ('User', 'Circle')
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;
