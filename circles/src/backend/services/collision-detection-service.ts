import { COLLISION_CONFIG } from '../config/collision.config.js';
import { Observe } from '../infrastructure/observer/index.js';
import { getRedisClient } from '../infrastructure/redis.js';
import { prisma } from '../lib/prisma.js';
import { makeCollisionKey } from '../utils/geo.util.js';

interface CandidateCircle {
  id: string;
  userId: string;
  radiusMeters: number;
  objective: string;
  distance_meters: number;
}

interface DetectedCollision {
  circle1Id: string | null; // Null when visitor doesn't have a circle
  circle2Id: string; // The circle being entered
  user1Id: string; // Visitor user
  user2Id: string; // Circle owner
  distance: number;
  timestamp: number;
}

/**
 * Service for collision detection using PostGIS spatial queries
 * Detects when user positions collide with other user circles
 */
export class CollisionDetectionService {
  /**
   * Detect all collisions for a user's position
   * Checks if user position falls within any other user's circles
   */
  @Observe({
    eventType: 'collision.detected',
    extractUserId: (args) => String(args[0]),
    buildMetadata: (_args, result) => {
      const collisions = Array.isArray(result) ? result : [];
      function isCollisionRecord(
        value: unknown,
      ): value is Record<string, unknown> {
        return typeof value === 'object' && value !== null;
      }
      return {
        collisionCount: collisions.length,
        collisions: collisions.map((c: unknown) => {
          if (isCollisionRecord(c)) {
            return {
              circleId: c.circle2Id,
              otherUserId: c.user2Id,
              distance: c.distance,
            };
          }
          return { circleId: null, otherUserId: null, distance: 0 };
        }),
      };
    },
  })
  async detectCollisionsForUser(
    userId: string,
    userLat: number,
    userLon: number
  ): Promise<DetectedCollision[]> {
    const allCollisions: DetectedCollision[] = [];

    try {
      // Get visitor's active circle - collisions only tracked if visitor has a circle
      const visitorCircle = await prisma.circle.findFirst({
        where: {
          userId,
          status: 'active',
          expiresAt: { gt: new Date() },
          startAt: { lte: new Date() },
        },
        select: { id: true },
      });

      // Skip collision detection if visitor has no active circle
      if (!visitorCircle) {
        return allCollisions;
      }

      // Query all circles owned by other users and check distances
      const candidates = await this.queryCandidateCirclesForPosition(
        userId,
        userLat,
        userLon
      );

      // Filter circles where user position is within the circle radius
      const actualCollisions = candidates.filter(
        (c) => c.distance_meters <= c.radiusMeters
      );

      // Take top N closest circles
      const topN = actualCollisions
        .sort((a, b) => a.distance_meters - b.distance_meters)
        .slice(0, COLLISION_CONFIG.MAX_COLLISIONS_PER_UPDATE);

      // Track each collision
      for (const collision of topN) {
        const detected: DetectedCollision = {
          circle1Id: visitorCircle.id, // Visitor's circle (guaranteed to exist here)
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
      console.error('Collision detection failed', {
        userId,
        error,
      });
    }

    return allCollisions;
  }

  /**
   * Query circles near a user's position using PostGIS
   * Joins with User table to get each circle owner's current position
   * Returns circles ordered by distance from user position
   */
  private async queryCandidateCirclesForPosition(
    userId: string,
    userLat: number,
    userLon: number
  ): Promise<CandidateCircle[]> {
    try {
      const result = await prisma.$queryRaw<CandidateCircle[]>`
        SELECT
          c.id,
          c."userId",
          c."radiusMeters",
          c.objective,
          ST_Distance(
            ST_MakePoint(${userLon}::float, ${userLat}::float)::geography,
            ST_MakePoint(u."centerLon", u."centerLat")::geography
          ) as distance_meters
        FROM "Circle" c
        INNER JOIN "User" u ON c."userId" = u.id
        WHERE c."userId" != ${userId}
          AND c.status = 'active'
          AND c."expiresAt" > NOW()
          AND c."startAt" <= NOW()
          AND u."centerLat" IS NOT NULL
          AND u."centerLon" IS NOT NULL
          AND ST_DWithin(
            ST_MakePoint(${userLon}::float, ${userLat}::float)::geography,
            ST_MakePoint(u."centerLon", u."centerLat")::geography,
            ${COLLISION_CONFIG.MAX_SEARCH_RADIUS_METERS}
          )
        ORDER BY distance_meters ASC
        LIMIT ${COLLISION_CONFIG.SPATIAL_INDEX_SEARCH_LIMIT}
      `;

      return result || [];
    } catch (error) {
      console.error('PostGIS query failed', { userId, error });
      return []; // Return empty array on query failure, continue processing
    }
  }

  /**
   * Track collision through stability window
   * Manage Redis state and create/update CollisionEvent in database
   */
  async trackCollisionStability(collision: DetectedCollision): Promise<void> {
    try {
      // Early return if circle1Id is null (shouldn't happen after refactor, but safety check)
      if (!collision.circle1Id) {
        console.warn("Attempted to track collision with null circle1Id", {
          collision,
        });
        return;
      }

      const redis = getRedisClient();

      // Generate collision key based on user pair and target circle
      // Since circle1Id can be null, use user IDs for uniqueness
      const key = collision.circle1Id
        ? makeCollisionKey(collision.circle1Id, collision.circle2Id)
        : `${collision.user1Id}:${collision.circle2Id}`;

      const redisKey = collision.circle1Id
        ? COLLISION_CONFIG.REDIS_KEYS.collisionActive(
            collision.circle1Id,
            collision.circle2Id
          )
        : `collision:active:${collision.user1Id}:${collision.circle2Id}`;

      // Get existing collision state
      const existing = await redis.hgetall(redisKey);

      if (!existing || Object.keys(existing).length === 0) {
        // First detection - initialize tracking and create CollisionEvent
        await redis.hset(redisKey, {
          firstSeenAt: collision.timestamp,
          detectedAt: collision.timestamp,
          status: "detecting",
          distance: collision.distance,
          user1Id: collision.user1Id,
          user2Id: collision.user2Id,
          circle2Id: collision.circle2Id,
        });

        // Add to stability queue
        await redis.zadd(
          COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
          collision.timestamp,
          key,
        );

        // Create CollisionEvent in database for persistence
        try {
          await prisma.collisionEvent.create({
            data: {
              circle1Id: collision.circle1Id,
              circle2Id: collision.circle2Id,
              user1Id: collision.user1Id,
              user2Id: collision.user2Id,
              distanceMeters: collision.distance,
              firstSeenAt: new Date(collision.timestamp),
              status: "detecting",
            },
          });
          console.debug("CollisionEvent created in database", {
            circle1Id: collision.circle1Id,
            circle2Id: collision.circle2Id,
          });
        } catch (dbError) {
          // Collision might already exist (duplicate detection)
          console.debug("CollisionEvent already exists or creation failed", {
            collision,
            error: dbError,
          });
        }
      } else {
        // Collision already tracked - update detection time in Redis and DB
        await redis.hset(redisKey, {
          detectedAt: collision.timestamp,
          distance: collision.distance,
        });

        // Update CollisionEvent in database
        try {
          await prisma.collisionEvent.update({
            where: {
              unique_collision_pair: {
                circle1Id: collision.circle1Id,
                circle2Id: collision.circle2Id,
              },
            },
            data: {
              detectedAt: new Date(collision.timestamp),
              distanceMeters: collision.distance,
            },
          });
        } catch (dbError) {
          console.warn("Failed to update CollisionEvent", {
            collision,
            error: dbError,
          });
        }
      }

      // Check if meets stability threshold
      const firstSeenAt = parseInt(
        existing?.firstSeenAt || String(collision.timestamp),
      );
      const duration = collision.timestamp - firstSeenAt;

      if (
        duration >= COLLISION_CONFIG.STABILITY_WINDOW_MS &&
        existing?.status !== "stable"
      ) {
        console.info("Collision promoted to stable", {
          collision,
          duration,
        });
        await redis.hset(redisKey, "status", "stable");

        // Update status in database
        try {
          await prisma.collisionEvent.update({
            where: {
              unique_collision_pair: {
                circle1Id: collision.circle1Id,
                circle2Id: collision.circle2Id,
              },
            },
            data: {
              status: "stable",
            },
          });
        } catch (dbError) {
          console.warn("Failed to update CollisionEvent to stable", {
            collision,
            error: dbError,
          });
        }
      }

      // Set TTL
      await redis.expire(redisKey, COLLISION_CONFIG.COLLISION_CACHE_TTL);
    } catch (error) {
      console.error("Failed to track collision stability", {
        collision,
        error,
      });
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
        "-inf",
        Date.now() - COLLISION_CONFIG.STABILITY_WINDOW_MS,
      );

      console.debug("Processing stability queue", {
        count: stableCollisionKeys.length,
      });

      for (const key of stableCollisionKeys) {
        try {
          // Check if still active
          const parts = key.split(":");
          if (parts.length < 2) {
            continue;
          }
          const circle1Id = parts[0] || "";
          const circle2Id = parts[1] || "";
          if (!circle1Id || !circle2Id) {
            continue;
          }
          const redisKey = COLLISION_CONFIG.REDIS_KEYS.collisionActive(
            circle1Id,
            circle2Id,
          );
          const state = await redis.hgetall(redisKey);

          if (!state || Object.keys(state).length === 0) {
            // Stale collision, remove from queue
            await redis.zrem(
              COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
              key,
            );
            continue;
          }

          // Status is tracked in Redis hash, ready for mission creation
          // This will be picked up by mission worker
        } catch (error) {
          console.error("Failed processing stability queue item", {
            key,
            error,
          });
        }
      }
    } catch (error) {
      console.error("Stability queue processing failed", { error });
    }
  }
}

export const collisionDetectionService = new CollisionDetectionService();
