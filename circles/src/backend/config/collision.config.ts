/**
 * Collision Detection & Matching System Configuration
 *
 * These constants control:
 * - Location update debouncing
 * - Collision stability window
 * - Cooldown periods
 * - Batch processing limits
 * - Cache TTLs
 */

export const COLLISION_CONFIG = {
  // ===== LOCATION DEBOUNCING =====
  // Skip location updates with insignificant movement
  MIN_MOVEMENT_METERS: 5,         // Minimum distance to trigger processing
  MIN_UPDATE_INTERVAL_MS: 2000,    // Minimum time between updates

  // ===== COLLISION STABILITY =====
  // Prevent false positives from GPS jitter
  STABILITY_WINDOW_MS: 30000,      // 30 seconds
  STALE_COLLISION_THRESHOLD_MS: 45000,  // 45 seconds (cleanup old collisions)

  // ===== COOLDOWNS =====
  // Prevent spam and allow time for reflection
  COOLDOWN_REJECTED_MS: 6 * 60 * 60 * 1000,        // 6 hours (user rejected)
  COOLDOWN_NOTIFIED_MS: 24 * 60 * 60 * 1000,       // 24 hours (user notified)
  COOLDOWN_MATCHED_MS: 7 * 24 * 60 * 60 * 1000,    // 7 days (match created)
  COOLDOWN_SAME_CIRCLES_MS: 3 * 60 * 60 * 1000,    // 3 hours (same circle pair)

  // ===== BATCH PROCESSING (N-CLOSEST MATCHES) =====
  // Optimize geospatial queries
  MAX_COLLISIONS_PER_UPDATE: 10,           // Process top 5 closest circles
  MAX_SEARCH_RADIUS_METERS: 5000,         // 5km initial spatial query radius
  SPATIAL_INDEX_SEARCH_LIMIT: 50,         // Candidate limit before filtering
  BATCH_PROCESSING_CONCURRENCY: 3,        // Parallel mission workers

  // ===== MISSION PROCESSING =====
  MISSION_TIMEOUT_MS: 15 * 60 * 1000,     // 15 minutes interview timeout
  MISSION_RETRY_ATTEMPTS: 3,              // Retry failed missions
  MISSION_RETRY_DELAY_MS: 2000,           // 2s exponential backoff

  // ===== CACHE TTLs (seconds) =====
  POSITION_CACHE_TTL: 300,                // User position (5 min)
  COLLISION_CACHE_TTL: 3600,              // Collision state (1 hour)
  USER_PROFILE_CACHE_TTL: 300,            // User profile for agents (5 min)
  CIRCLE_CACHE_TTL: 600,                  // Circle data (10 min)
  IN_FLIGHT_MISSION_TTL: 900,             // In-progress mission marker (15 min)

  // ===== REDIS KEY PREFIXES =====
  REDIS_KEYS: {
    position: (userId: string) => `position:${userId}`,
    collisionActive: (circle1Id: string, circle2Id: string) =>
      `collisions:active:${[circle1Id, circle2Id].sort().join(':')}`,
    collisionStabilityQueue: 'collisions:stability_queue',
    cooldown: (user1Id: string, user2Id: string) =>
      `cooldowns:${[user1Id, user2Id].sort().join(':')}`,
    cooldownCircles: (circle1Id: string, circle2Id: string) =>
      `cooldowns:circles:${[circle1Id, circle2Id].sort().join(':')}`,
    inFlightMission: (user1Id: string, user2Id: string) =>
      `missions:in_flight:${[user1Id, user2Id].sort().join(':')}`,
    missionLock: (user1Id: string, user2Id: string) =>
      `locks:mission:${[user1Id, user2Id].sort().join(':')}`,
  }
} as const;

// Type safety: ensure TTL values are positive
Object.entries(COLLISION_CONFIG).forEach(([key, value]) => {
  if (typeof value === 'number' && key.includes('TTL') && value <= 0) {
    throw new Error(`Invalid TTL value for ${key}: ${value}`);
  }
});
