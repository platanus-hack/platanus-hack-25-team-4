import { COLLISION_CONFIG } from '../config/collision.config.js';
import { getRedisClient } from '../infrastructure/redis.js';
import { prisma } from '../lib/prisma.js';
import type { Circle } from '../types/index.js';
import { makeCollisionKey } from '../utils/geo.util.js';

interface CandidateCircle {
  id: string;
  userId: string;
  radiusMeters: number;
  objective: string;
  distance_meters: number;
}

interface DetectedCollision {
  circle1Id: string;
  circle2Id: string;
  user1Id: string;
  user2Id: string;
  distance: number;
  timestamp: number;
}

interface CircleWithLocation extends Circle {
  centerLat: number;
  centerLon: number;
}

function getNumericProperty(obj: unknown, key: string): number | undefined {
  if (typeof obj !== 'object' || obj === null) {
    return undefined;
  }
  if (!(key in obj)) {
    return undefined;
  }
  const value = Object.getOwnPropertyDescriptor(obj, key)?.value;
  return typeof value === 'number' ? value : undefined;
}

function hasLocation(circle: Circle): circle is CircleWithLocation {
  const centerLat = getNumericProperty(circle, 'centerLat');
  const centerLon = getNumericProperty(circle, 'centerLon');
  return centerLat !== undefined && centerLon !== undefined;
}

/**
 * Service for collision detection using PostGIS spatial queries
 * Detects when user positions collide with other user circles
 */
export class CollisionDetectionService {
  /**
   * Detect all collisions for user's circles
   * Uses batch PostGIS query for efficiency
   */
  async detectCollisionsForUser(
    userId: string,
    circles: Circle[]
  ): Promise<DetectedCollision[]> {
    const allCollisions: DetectedCollision[] = [];

    for (const circle of circles) {
      try {
        // PostGIS query to find candidate circles nearby
        const candidates = await this.queryCandidateCircles(circle);

        // Filter by collision distance using a single circle:
        // other users are treated as points, and we only check
        // whether they lie within this circle's radius.
        const actualCollisions = candidates.filter(
          (c) =>
            circle.radiusMeters !== null &&
            c.distance_meters <= circle.radiusMeters
        );

        // Take top N by distance
        const topN = actualCollisions
          .sort((a, b) => a.distance_meters - b.distance_meters)
          .slice(0, COLLISION_CONFIG.MAX_COLLISIONS_PER_UPDATE);

        // Track each collision
        for (const collision of topN) {
          const detected: DetectedCollision = {
            circle1Id: circle.id,
            circle2Id: collision.id,
            user1Id: userId,
            user2Id: collision.userId,
            distance: collision.distance_meters,
            timestamp: Date.now(),
          };

          allCollisions.push(detected);
          await this.trackCollisionStability(detected);
        }
      } catch (error) {
        console.error('Collision detection failed for circle', {
          circleId: circle.id,
          error,
        });
        // Continue with other circles
      }
    }

    return allCollisions;
  }

  /**
   * Query nearest circles using PostGIS
   * Returns ~50 candidates, filtered with bounding box
   */
  private async queryCandidateCircles(circle: Circle): Promise<CandidateCircle[]> {
    if (!hasLocation(circle) || circle.radiusMeters === null) {
      return [];
    }

    try {
      const result = await prisma.$queryRaw<CandidateCircle[]>`
        SELECT
          c.id,
          c."userId",
          c."radiusMeters",
          c.objective,
          ST_Distance(
            ST_MakePoint(${circle.centerLon}::float, ${circle.centerLat}::float)::geography,
            ST_MakePoint(c."centerLon", c."centerLat")::geography
          ) as distance_meters
        FROM "Circle" c
        WHERE c."userId" != ${circle.userId}
          AND c.status = 'active'
          AND c."expiresAt" > NOW()
          AND c."startAt" <= NOW()
          AND ST_DWithin(
            ST_MakePoint(${circle.centerLon}::float, ${circle.centerLat}::float)::geography,
            ST_MakePoint(c."centerLon", c."centerLat")::geography,
            ${COLLISION_CONFIG.MAX_SEARCH_RADIUS_METERS}
          )
        ORDER BY distance_meters ASC
        LIMIT ${COLLISION_CONFIG.SPATIAL_INDEX_SEARCH_LIMIT}
      `;

      return result || [];
    } catch (error) {
      console.error('PostGIS query failed', { circleId: circle.id, error });
      return []; // Return empty array on query failure, continue processing
    }
  }

  /**
   * Track collision through stability window
   * Manage Redis state for stability assessment
   */
  async trackCollisionStability(collision: DetectedCollision): Promise<void> {
    try {
      const redis = getRedisClient();
      const key = makeCollisionKey(collision.circle1Id, collision.circle2Id);
      const redisKey = COLLISION_CONFIG.REDIS_KEYS.collisionActive(
        collision.circle1Id,
        collision.circle2Id
      );

      // Get existing collision state
      const existing = await redis.hgetall(redisKey);

      if (!existing || Object.keys(existing).length === 0) {
        // First detection - initialize tracking
        await redis.hset(redisKey, {
          firstSeenAt: collision.timestamp,
          detectedAt: collision.timestamp,
          status: 'detecting',
          distance: collision.distance,
        });

        // Add to stability queue
        await redis.zadd(
          COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
          collision.timestamp,
          key
        );
      } else {
        // Collision already tracked - update detection time
        await redis.hset(redisKey, {
          detectedAt: collision.timestamp,
          distance: collision.distance,
        });
      }

      // Check if meets stability threshold
      const firstSeenAt =
        parseInt(existing?.firstSeenAt || String(collision.timestamp));
      const duration = collision.timestamp - firstSeenAt;

      if (
        duration >= COLLISION_CONFIG.STABILITY_WINDOW_MS &&
        existing?.status !== 'stable'
      ) {
        console.info('Collision promoted to stable', {
          collision,
          duration,
        });
        await redis.hset(redisKey, 'status', 'stable');
      }

      // Set TTL
      await redis.expire(redisKey, COLLISION_CONFIG.COLLISION_CACHE_TTL);
    } catch (error) {
      console.error('Failed to track collision stability', { collision, error });
      // Don't throw - continue processing
    }
  }

  /**
   * Process stability queue periodically
   * Promoted stable collisions to mission creation
   */
  async processStabilityQueue(): Promise<void> {
    try {
      const redis = getRedisClient();

      // Get collisions older than stability window
      const stableCollisionKeys = await redis.zrangebyscore(
        COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
        '-inf',
        Date.now() - COLLISION_CONFIG.STABILITY_WINDOW_MS
      );

      console.debug('Processing stability queue', {
        count: stableCollisionKeys.length,
      });

      for (const key of stableCollisionKeys) {
        try {
          // Check if still active
          const parts = key.split(':');
          if (parts.length < 2) {
            continue;
          }
          const circle1Id = parts[0] || '';
          const circle2Id = parts[1] || '';
          if (!circle1Id || !circle2Id) {
            continue;
          }
          const redisKey = COLLISION_CONFIG.REDIS_KEYS.collisionActive(circle1Id, circle2Id);
          const state = await redis.hgetall(redisKey);

          if (!state || Object.keys(state).length === 0) {
            // Stale collision, remove from queue
            await redis.zrem(
              COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
              key
            );
            continue;
          }

          // Status is tracked in Redis hash, ready for mission creation
          // This will be picked up by mission worker
        } catch (error) {
          console.error('Failed processing stability queue item', {
            key,
            error,
          });
        }
      }
    } catch (error) {
      console.error('Stability queue processing failed', { error });
    }
  }
}

export const collisionDetectionService = new CollisionDetectionService();
