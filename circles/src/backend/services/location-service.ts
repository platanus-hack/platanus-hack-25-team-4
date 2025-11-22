import { COLLISION_CONFIG } from '../config/collision.config.js';
import { getRedisClient } from '../infrastructure/redis.js';
import { prisma } from '../lib/prisma.js';
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

      // 3. Update circle centers
      const userCircles = await this.updateCircleCenters(userId, latitude, longitude);
      if (userCircles.length === 0) {
        return { skipped: true, collisionsDetected: 0 };
      }

      console.info('Location update processed', {
        userId,
        circleCount: userCircles.length,
        location: { latitude, longitude },
      });

      return { skipped: false, collisionsDetected: 0 };
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

  /**
   * Update circle center coordinates in database
   * Called when user location changes significantly
   */
  private async updateCircleCenters(
    userId: string,
    lat: number,
    lon: number
  ): Promise<{ id: string }[]> {
    try {
      // Update all active circles for this user
      await prisma.circle.updateMany({
        where: {
          userId,
          status: 'active',
          expiresAt: { gt: new Date() },
        },
        data: {
          centerLat: lat,
          centerLon: lon,
        },
      });

      // Fetch updated circles for return
      const updated = await prisma.circle.findMany({
        where: { userId, status: 'active' },
        select: { id: true, centerLat: true, centerLon: true },
      });

      console.debug('Circle centers updated', { userId, count: updated.length });
      return updated;
    } catch (error) {
      console.error('Failed to update circle centers', { userId, error });
      throw error;
    }
  }
}

export const locationService = new LocationService();
