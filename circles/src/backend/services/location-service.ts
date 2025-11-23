import { collisionDetectionService } from "./collision-detection-service.js";
import { COLLISION_CONFIG } from "../config/collision.config.js";
import { getRedisClient } from "../infrastructure/redis.js";
import { prisma } from "../lib/prisma.js";
import { haversineDistance } from "../utils/geo.util.js";
import { logger } from "../utils/logger.util.js";

/**
 * Service for handling location updates and debouncing
 * Manages user position caching and triggers collision detection
 */
export class LocationService {
  // In-memory cache for faster debounce checks
  private lastCachedPosition = new Map<
    string,
    { lat: number; lon: number; timestamp: number }
  >();

  /**
   * Main entry point: Process user location update
   * Returns: result with processing status and collision count if detected
   */
  async updateUserLocation(
    userId: string,
    latitude: number,
    longitude: number,
    accuracy: number,
    timestamp: Date,
  ): Promise<{
    skipped: boolean;
    collisionsDetected?: number;
    error?: string;
  }> {
    const startTime = Date.now();
    logger.info("[COLLISION_PIPELINE] Location update received", {
      userId,
      location: { latitude, longitude, accuracy },
      timestamp: timestamp.toISOString(),
      receivedAt: new Date().toISOString(),
    });

    try {
      // 1. Debounce check
      logger.debug("[COLLISION_PIPELINE] Starting debounce check", { userId });
      if (!this.shouldProcessUpdate(userId, latitude, longitude, timestamp)) {
        logger.debug("[COLLISION_PIPELINE] Location update skipped by debounce", {
          userId,
          location: { latitude, longitude },
          reason: "Failed debounce check - likely too frequent or insufficient movement",
        });
        return { skipped: true };
      }
      logger.debug("[COLLISION_PIPELINE] Debounce check passed", { userId });

      // 2. Update User position in database (circles reference this)
      logger.debug("[COLLISION_PIPELINE] Updating user position in database", {
        userId,
        location: { latitude, longitude },
      });
      await this.updateUserPositionInDB(userId, latitude, longitude);
      logger.debug("[COLLISION_PIPELINE] User position updated in database", {
        userId,
      });

      // 3. Update cache
      logger.debug("[COLLISION_PIPELINE] Updating user position cache", {
        userId,
        accuracy,
      });
      await this.cacheUserPosition(userId, latitude, longitude, accuracy);
      logger.debug("[COLLISION_PIPELINE] User position cached", { userId });

      // 4. Detect collisions with other users' circles
      logger.info("[COLLISION_PIPELINE] Starting collision detection", {
        userId,
        location: { latitude, longitude },
      });
      const collisions =
        await collisionDetectionService.detectCollisionsForUser(
          userId,
          latitude,
          longitude,
        );
      logger.info("[COLLISION_PIPELINE] Collision detection completed", {
        userId,
        collisionsDetected: collisions.length,
        collisions: collisions.map((c) => ({
          circle2Id: c.circle2Id,
          user2Id: c.user2Id,
          distance: c.distance,
        })),
      });

      const duration = Date.now() - startTime;
      logger.info("[COLLISION_PIPELINE] Location update processed successfully", {
        userId,
        collisionsDetected: collisions.length,
        location: { latitude, longitude },
        durationMs: duration,
      });

      return { skipped: false, collisionsDetected: collisions.length };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Unknown error";
      const duration = Date.now() - startTime;
      logger.error("[COLLISION_PIPELINE] Location update failed", error);
      logger.debug("[COLLISION_PIPELINE] Error details", {
        userId,
        errorMsg,
        durationMs: duration,
        stack: error instanceof Error ? error.stack : undefined,
      });
      return { skipped: true, error: errorMsg };
    }
  }

  /**
   * Check if location update should be processed
   * Returns true if: movement >= 20m AND time delta >= 3s
   */
  private shouldProcessUpdate(
    userId: string,
    newLat: number,
    newLon: number,
    timestamp: Date,
  ): boolean {
    // Check timestamp age (reject updates older than 30 seconds)
    const timeDelta = Date.now() - timestamp.getTime();
    if (timeDelta > 30000) {
      logger.debug("[COLLISION_PIPELINE] Debounce: timestamp too old", {
        userId,
        timeDelta,
        maxAllowed: 30000,
      });
      return false;
    }

    // Get last cached position
    const lastPosition = this.lastCachedPosition.get(userId);
    if (!lastPosition) {
      logger.debug("[COLLISION_PIPELINE] Debounce: first location update for user", {
        userId,
      });
      return true; // First update, always process
    }

    // Check time interval
    const timeSinceLastUpdate = Date.now() - lastPosition.timestamp;
    if (timeSinceLastUpdate < COLLISION_CONFIG.MIN_UPDATE_INTERVAL_MS) {
      logger.debug("[COLLISION_PIPELINE] Debounce: update too frequent", {
        userId,
        timeSinceLastUpdate,
        minRequired: COLLISION_CONFIG.MIN_UPDATE_INTERVAL_MS,
      });
      return false; // Too frequent
    }

    // Check movement distance
    const distance = haversineDistance(
      lastPosition.lat,
      lastPosition.lon,
      newLat,
      newLon,
    );

    const minMovement = COLLISION_CONFIG.MIN_MOVEMENT_METERS;
    const shouldProcess = distance >= minMovement;
    
    logger.debug("[COLLISION_PIPELINE] Debounce: movement check", {
      userId,
      distance,
      minRequired: minMovement,
      timeSinceLastUpdate,
      willProcess: shouldProcess,
    });

    return shouldProcess;
  }

  /**
   * Update User position in database
   * Circles reference User.centerLat/centerLon as their center point
   */
  private async updateUserPositionInDB(
    userId: string,
    lat: number,
    lon: number,
  ): Promise<void> {
    try {
      logger.debug("[COLLISION_PIPELINE] DB: Updating user position", {
        userId,
        location: { lat, lon },
      });
      await prisma.user.update({
        where: { id: userId },
        data: {
          centerLat: lat,
          centerLon: lon,
        },
      });
      logger.debug("[COLLISION_PIPELINE] DB: User position updated successfully", {
        userId,
        location: { lat, lon },
      });
    } catch (error) {
      logger.error("[COLLISION_PIPELINE] DB: Failed to update user position", error);
      logger.debug("[COLLISION_PIPELINE] DB error details", {
        userId,
        location: { lat, lon },
      });
      // Don't throw - continue processing even if DB update fails
    }
  }

  /**
   * Cache user position in Redis for quick debounce checks
   */
  private async cacheUserPosition(
    userId: string,
    lat: number,
    lon: number,
    accuracy: number,
  ): Promise<void> {
    try {
      const redis = getRedisClient();
      const key = COLLISION_CONFIG.REDIS_KEYS.position(userId);
      const cachedAt = Date.now();

      logger.debug("[COLLISION_PIPELINE] Cache: Setting user position in Redis", {
        userId,
        location: { lat, lon, accuracy },
        ttl: COLLISION_CONFIG.POSITION_CACHE_TTL,
      });

      await redis.set(
        key,
        JSON.stringify({ lat, lon, accuracy, timestamp: cachedAt }),
        "EX",
        COLLISION_CONFIG.POSITION_CACHE_TTL,
      );

      // Also maintain in-memory cache for faster debounce checks
      this.lastCachedPosition.set(userId, {
        lat,
        lon,
        timestamp: cachedAt,
      });

      logger.debug("[COLLISION_PIPELINE] Cache: User position cached successfully", {
        userId,
        ttl: COLLISION_CONFIG.POSITION_CACHE_TTL,
      });
    } catch (error) {
      logger.error("[COLLISION_PIPELINE] Cache: Failed to cache user position", error);
      logger.debug("[COLLISION_PIPELINE] Cache error details", {
        userId,
        location: { lat, lon, accuracy },
      });
      // Don't throw - continue processing even if cache fails
    }
  }
}

export const locationService = new LocationService();
