import { collisionDetectionService } from './collision-detection-service.js';
import { COLLISION_CONFIG } from '../config/collision.config.js';
import { Observe } from '../infrastructure/observer/index.js';
import { getRedisClient } from '../infrastructure/redis.js';
import { haversineDistance } from '../utils/geo.util.js';

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
  @Observe({
    eventType: 'location.updated',
    extractUserId: (args) => String(args[0]),
    buildMetadata: (args, result) => {
      let skipped = false;
      let collisionsDetected: unknown = undefined;

      if (result && typeof result === 'object' && 'skipped' in result) {
        const res: Record<string, unknown> = result;
        skipped = Boolean(res.skipped);
        collisionsDetected = res.collisionsDetected;
      }

      return {
        latitude: args[1],
        longitude: args[2],
        accuracy: args[3],
        timestamp: args[4],
        skipped,
        collisionsDetected,
      };
    },
  })
  async updateUserLocation(
    userId: string,
    latitude: number,
    longitude: number,
    accuracy: number,
    timestamp: Date
  ): Promise<{ skipped: boolean; collisionsDetected?: number; error?: string }> {
    try {
      // 1. Debounce check
      if (!this.shouldProcessUpdate(userId, latitude, longitude, timestamp)) {
        return { skipped: true };
      }

      // 2. Update cache
      await this.cacheUserPosition(userId, latitude, longitude, accuracy);

      // 3. Detect collisions with other users' circles
      // Note: User position should already be in DB via PUT /users/position endpoint
      const collisions = await collisionDetectionService.detectCollisionsForUser(
        userId,
        latitude,
        longitude
      );

      console.info('Location update processed', {
        userId,
        collisionsDetected: collisions.length,
        location: { latitude, longitude },
      });

      return { skipped: false, collisionsDetected: collisions.length };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error';
      console.error('Location update failed', { userId, error: errorMsg });
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
    timestamp: Date
  ): boolean {
    // Check timestamp age (reject updates older than 30 seconds)
    const timeDelta = Date.now() - timestamp.getTime();
    if (timeDelta > 30000) {
      console.warn('Location update timestamp too old', { userId, timeDelta });
      return false;
    }

    // Get last cached position
    const lastPosition = this.lastCachedPosition.get(userId);
    if (!lastPosition) {
      return true; // First update, always process
    }

    // Check time interval
    if (Date.now() - lastPosition.timestamp < COLLISION_CONFIG.MIN_UPDATE_INTERVAL_MS) {
      return false; // Too frequent
    }

    // Check movement distance
    const distance = haversineDistance(
      lastPosition.lat,
      lastPosition.lon,
      newLat,
      newLon
    );

    return distance >= COLLISION_CONFIG.MIN_MOVEMENT_METERS;
  }

  /**
   * Cache user position in Redis for quick debounce checks
   */
  private async cacheUserPosition(
    userId: string,
    lat: number,
    lon: number,
    accuracy: number
  ): Promise<void> {
    try {
      const redis = getRedisClient();
      const key = COLLISION_CONFIG.REDIS_KEYS.position(userId);

      await redis.set(
        key,
        JSON.stringify({ lat, lon, accuracy, timestamp: Date.now() }),
        'EX',
        COLLISION_CONFIG.POSITION_CACHE_TTL
      );

      // Also maintain in-memory cache for faster debounce checks
      this.lastCachedPosition.set(userId, {
        lat,
        lon,
        timestamp: Date.now(),
      });
    } catch (error) {
      console.error('Failed to cache user position', { userId, error });
      // Don't throw - continue processing even if cache fails
    }
  }

}

export const locationService = new LocationService();
