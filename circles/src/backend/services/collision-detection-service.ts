import { COLLISION_CONFIG } from "../config/collision.config.js";
import { getRedisClient } from "../infrastructure/redis.js";
import { prisma } from "../lib/prisma.js";
import { makeCollisionKey } from "../utils/geo.util.js";
import { logger } from "../utils/logger.util.js";

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
  async detectCollisionsForUser(
    userId: string,
    userLat: number,
    userLon: number,
  ): Promise<DetectedCollision[]> {
    const allCollisions: DetectedCollision[] = [];
    const startTime = Date.now();

    logger.info("[COLLISION_DETECTION] Starting collision detection", {
      userId,
      location: { userLat, userLon },
    });

    try {
      // Query all circles owned by other users and check distances
      logger.debug("[COLLISION_DETECTION] Querying candidate circles", {
        userId,
        searchRadius: COLLISION_CONFIG.MAX_SEARCH_RADIUS_METERS,
      });
      const candidates = await this.queryCandidateCirclesForPosition(
        userId,
        userLat,
        userLon,
      );
      logger.info("[COLLISION_DETECTION] Candidate circles found", {
        userId,
        candidateCount: candidates.length,
        candidates: candidates.map((c) => ({
          circleId: c.id,
          userId: c.userId,
          distance: c.distance_meters,
          radius: c.radiusMeters,
        })),
      });

      // Filter circles where user position is within the circle radius
      const actualCollisions = candidates.filter(
        (c) => c.distance_meters <= c.radiusMeters,
      );
      logger.info("[COLLISION_DETECTION] Actual collisions detected", {
        userId,
        actualCollisionCount: actualCollisions.length,
        actualCollisions: actualCollisions.map((c) => ({
          circleId: c.id,
          userId: c.userId,
          distance: c.distance_meters,
          radius: c.radiusMeters,
        })),
      });

      // Take top N closest circles
      const topN = actualCollisions
        .sort((a, b) => a.distance_meters - b.distance_meters)
        .slice(0, COLLISION_CONFIG.MAX_COLLISIONS_PER_UPDATE);
      logger.info("[COLLISION_DETECTION] Taking top N collisions", {
        userId,
        topNCount: topN.length,
        maxAllowed: COLLISION_CONFIG.MAX_COLLISIONS_PER_UPDATE,
      });

      // Track each collision
      for (const collision of topN) {
        // Find visitor's active circle for CollisionEvent persistence
        // The visitor doesn't need a circle to detect collision, but we need one for DB
        logger.debug("[COLLISION_DETECTION] Looking for visitor's active circle", {
          visitorUserId: userId,
          targetCircleId: collision.id,
        });
        const visitorCircle = await prisma.circle.findFirst({
          where: {
            userId: userId,
            status: "active",
            expiresAt: { gt: new Date() },
            startAt: { lte: new Date() },
          },
          orderBy: { createdAt: "desc" },
        });

        if (!visitorCircle) {
          // Visitor has no active circles - skip persistence but continue detection
          logger.warn(
            "[COLLISION_DETECTION] Visitor has no active circle, skipping collision persistence",
            {
              visitorUserId: userId,
              targetCircleId: collision.id,
              targetUserId: collision.userId,
            },
          );
          continue;
        }

        const detected: DetectedCollision = {
          circle1Id: visitorCircle.id, // Use visitor's circle for DB persistence
          circle2Id: collision.id,
          user1Id: userId,
          user2Id: collision.userId,
          distance: collision.distance_meters,
          timestamp: Date.now(),
        };

        allCollisions.push(detected);
        logger.info("[COLLISION_DETECTION] Tracking collision stability", {
          circle1Id: detected.circle1Id,
          circle2Id: detected.circle2Id,
          distance: detected.distance,
        });
        await this.trackCollisionStability(detected);
      }
      
      const duration = Date.now() - startTime;
      logger.info("[COLLISION_DETECTION] Collision detection completed", {
        userId,
        totalCollisionsProcessed: allCollisions.length,
        durationMs: duration,
      });
    } catch (error) {
      const duration = Date.now() - startTime;
      logger.error("[COLLISION_DETECTION] Collision detection failed", error);
      logger.debug("[COLLISION_DETECTION] Error details", {
        userId,
        durationMs: duration,
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
    userLon: number,
  ): Promise<CandidateCircle[]> {
    const startTime = Date.now();
    try {
      logger.debug("[COLLISION_DETECTION] PostGIS: Executing spatial query", {
        userId,
        location: { userLat, userLon },
        searchRadius: COLLISION_CONFIG.MAX_SEARCH_RADIUS_METERS,
        resultLimit: COLLISION_CONFIG.SPATIAL_INDEX_SEARCH_LIMIT,
      });

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

      const duration = Date.now() - startTime;
      logger.debug("[COLLISION_DETECTION] PostGIS: Query completed", {
        userId,
        resultCount: result?.length || 0,
        durationMs: duration,
        results: result?.map((r) => ({
          circleId: r.id,
          userId: r.userId,
          distance: r.distance_meters,
          radius: r.radiusMeters,
        })),
      });

      return result || [];
    } catch (error) {
      const duration = Date.now() - startTime;
      logger.error("[COLLISION_DETECTION] PostGIS query failed", error);
      logger.debug("[COLLISION_DETECTION] PostGIS error details", {
        userId,
        location: { userLat, userLon },
        durationMs: duration,
      });
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
        logger.warn("[COLLISION_TRACKING] Attempted to track collision with null circle1Id", {
          collision,
        });
        return;
      }

      logger.debug("[COLLISION_TRACKING] Starting collision tracking", {
        circle1Id: collision.circle1Id,
        circle2Id: collision.circle2Id,
        distance: collision.distance,
      });

      const redis = getRedisClient();

      // Generate collision key based on circle pair
      const key = makeCollisionKey(collision.circle1Id, collision.circle2Id);
      const redisKey = COLLISION_CONFIG.REDIS_KEYS.collisionActive(
        collision.circle1Id,
        collision.circle2Id,
      );

      // Get existing collision state
      logger.debug("[COLLISION_TRACKING] Checking for existing collision state", {
        redisKey,
      });
      const existing = await redis.hgetall(redisKey);

      if (!existing || Object.keys(existing).length === 0) {
        // First detection - initialize tracking and create CollisionEvent
        logger.info("[COLLISION_TRACKING] First detection - initializing tracking", {
          circle1Id: collision.circle1Id,
          circle2Id: collision.circle2Id,
        });

        await redis.hset(redisKey, {
          firstSeenAt: collision.timestamp,
          detectedAt: collision.timestamp,
          status: "detecting",
          distance: collision.distance,
          user1Id: collision.user1Id,
          user2Id: collision.user2Id,
          circle1Id: collision.circle1Id,
          circle2Id: collision.circle2Id,
        });
        logger.debug("[COLLISION_TRACKING] Redis state initialized", {
          circle1Id: collision.circle1Id,
          circle2Id: collision.circle2Id,
        });

        // Add to stability queue
        logger.debug("[COLLISION_TRACKING] Adding to stability queue", {
          key,
          timestamp: collision.timestamp,
        });
        await redis.zadd(
          COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
          collision.timestamp,
          key,
        );

        // Create CollisionEvent in database for persistence
        try {
          logger.debug("[COLLISION_TRACKING] Creating CollisionEvent in database", {
            circle1Id: collision.circle1Id,
            circle2Id: collision.circle2Id,
          });
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
          logger.info("[COLLISION_TRACKING] CollisionEvent created in database", {
            circle1Id: collision.circle1Id,
            circle2Id: collision.circle2Id,
          });
        } catch (dbError) {
          // Collision might already exist (duplicate detection)
          logger.debug("[COLLISION_TRACKING] CollisionEvent already exists or creation failed", dbError);
        }
      } else {
        // Collision already tracked - update detection time in Redis and DB
        logger.debug("[COLLISION_TRACKING] Existing collision detected - updating", {
          circle1Id: collision.circle1Id,
          circle2Id: collision.circle2Id,
          currentStatus: existing.status,
          timeSinceFirstSeen: collision.timestamp - parseInt(existing.firstSeenAt || "0"),
        });

        await redis.hset(redisKey, {
          detectedAt: collision.timestamp,
          distance: collision.distance,
        });
        logger.debug("[COLLISION_TRACKING] Redis state updated", {
          circle1Id: collision.circle1Id,
          circle2Id: collision.circle2Id,
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
          logger.debug("[COLLISION_TRACKING] CollisionEvent updated in database", {
            circle1Id: collision.circle1Id,
            circle2Id: collision.circle2Id,
          });
        } catch (dbError) {
          logger.warn("[COLLISION_TRACKING] Failed to update CollisionEvent", dbError);
        }
      }

      // Check if meets stability threshold
      const firstSeenAt = parseInt(
        existing?.firstSeenAt || String(collision.timestamp),
      );
      const duration = collision.timestamp - firstSeenAt;
      const stabilityThreshold = COLLISION_CONFIG.STABILITY_WINDOW_MS;

      logger.debug("[COLLISION_TRACKING] Checking stability threshold", {
        circle1Id: collision.circle1Id,
        circle2Id: collision.circle2Id,
        duration,
        threshold: stabilityThreshold,
        isStable: duration >= stabilityThreshold,
        currentStatus: existing?.status,
      });

      if (
        duration >= stabilityThreshold &&
        existing?.status !== "stable"
      ) {
        logger.info("[COLLISION_TRACKING] Collision promoted to stable", {
          circle1Id: collision.circle1Id,
          circle2Id: collision.circle2Id,
          duration,
          threshold: stabilityThreshold,
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
          logger.info("[COLLISION_TRACKING] CollisionEvent status updated to stable", {
            circle1Id: collision.circle1Id,
            circle2Id: collision.circle2Id,
          });
        } catch (dbError) {
          logger.warn("[COLLISION_TRACKING] Failed to update CollisionEvent to stable", dbError);
        }
      }

      // Set TTL
      await redis.expire(redisKey, COLLISION_CONFIG.COLLISION_CACHE_TTL);
      logger.debug("[COLLISION_TRACKING] Redis key TTL set", {
        circle1Id: collision.circle1Id,
        circle2Id: collision.circle2Id,
        ttl: COLLISION_CONFIG.COLLISION_CACHE_TTL,
      });
    } catch (error) {
      logger.error("[COLLISION_TRACKING] Failed to track collision stability", error);
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

      logger.debug("Processing stability queue", {
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
          logger.error("Failed processing stability queue item", error);
          logger.debug("Failed queue item key", { key });
        }
      }
    } catch (error) {
      logger.error("Stability queue processing failed", error);
    }
  }
}

export const collisionDetectionService = new CollisionDetectionService();
