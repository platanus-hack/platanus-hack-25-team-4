import { COLLISION_CONFIG } from "../config/collision.config.js";
import { getRedisClient } from "../infrastructure/redis.js";
import { prisma } from "../lib/prisma.js";
import { agentMatchService } from "../services/agent-match-service.js";
import { logger } from "../utils/logger.util.js";

/**
 * Stability Queue Worker
 *
 * Runs every 5 seconds to:
 * 1. Process stability queue - promote collisions that have been stable for 30s
 * 2. Create missions for promoted collisions
 * 3. Clean up stale collisions older than 45s
 */
export class StabilityWorker {
  private isRunning = false;

  /**
   * Start the stability worker (runs every 5 seconds)
   */
  start(intervalMs: number = 5000): void {
    if (this.isRunning) {
      logger.warn("Stability worker is already running");
      return;
    }

    this.isRunning = true;
    logger.info("Starting stability worker with interval", { intervalMs });

    // Run immediately on start
    this.tick().catch((error) => {
      logger.error("Stability worker error on initial tick", { error });
    });

    // Then run at intervals
    setInterval(() => {
      this.tick().catch((error) => {
        logger.error("Stability worker error", { error });
      });
    }, intervalMs);
  }

  /**
   * Main tick function - process stability queue and cleanup
   */
  private async tick(): Promise<void> {
    const tickStartTime = Date.now();
    try {
      const redis = getRedisClient();
      const now = Date.now();

      // Step 1: Get collisions from stability queue
      logger.debug("[STABILITY_WORKER] Tick started", {
        timestamp: new Date(now).toISOString(),
      });

      logger.debug("[STABILITY_WORKER] Fetching stability queue", {
        timestamp: new Date(now).toISOString(),
      });
      const stableCollisions = await redis.zrange(
        COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
        0,
        -1,
      );

      logger.info("[STABILITY_WORKER] Stability queue size", {
        queueSize: stableCollisions.length,
        timestamp: new Date(now).toISOString(),
      });

      // Step 2: Process each stable collision
      let processedCount = 0;
      let missionsCreated = 0;

      for (const collisionKey of stableCollisions) {
        try {
          logger.debug("[STABILITY_WORKER] Processing collision from queue", {
            collisionKey,
          });

          // Get collision details from Redis
          const [circle1IdPart, circle2IdPart] = collisionKey.split(":");
          const collisionData = await redis.hgetall(
            COLLISION_CONFIG.REDIS_KEYS.collisionActive(
              circle1IdPart!,
              circle2IdPart!,
            ),
          );

          if (!collisionData || Object.keys(collisionData).length === 0) {
            // Collision data expired, remove from queue
            logger.debug("[STABILITY_WORKER] Collision data expired in Redis, removing from queue", {
              collisionKey,
            });
            await redis.zrem(
              COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
              collisionKey,
            );
            continue;
          }

          const firstSeenAt = parseInt(collisionData.firstSeenAt || "0");
          const stabilityDuration = now - firstSeenAt;

          logger.debug("[STABILITY_WORKER] Checking collision stability", {
            collisionKey,
            firstSeenAt,
            now,
            stabilityDuration,
            threshold: COLLISION_CONFIG.STABILITY_WINDOW_MS,
            isStable: stabilityDuration >= COLLISION_CONFIG.STABILITY_WINDOW_MS,
            currentStatus: collisionData.status,
          });

          // Check if collision has been stable for 30 seconds
          if (stabilityDuration >= COLLISION_CONFIG.STABILITY_WINDOW_MS) {
            // Promote collision to mission creation
            const circle1Id = collisionData.circle1Id;
            const circle2Id = collisionData.circle2Id;

            logger.info("[STABILITY_WORKER] Collision is stable, promoting to mission creation", {
              circle1Id,
              circle2Id,
              collisionKey,
              stabilityDuration,
            });

            if (!circle1Id || !circle2Id) {
              logger.warn("[STABILITY_WORKER] Missing circle IDs in collision data, skipping", {
                collisionData,
                collisionKey,
              });
              await redis.zrem(
                COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
                collisionKey,
              );
              continue;
            }

            // Get collision event from database
            logger.debug("[STABILITY_WORKER] Fetching CollisionEvent from database", {
              circle1Id,
              circle2Id,
            });
            const collisionEvent = await prisma.collisionEvent.findUnique({
              where: {
                unique_collision_pair: { circle1Id, circle2Id },
              },
            });

            if (!collisionEvent) {
              logger.warn(
                "[STABILITY_WORKER] CollisionEvent not found in database - may have been created with null circle1Id",
                {
                  circle1Id,
                  circle2Id,
                  collisionKey,
                },
              );
              await redis.zrem(
                COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
                collisionKey,
              );
              continue;
            }

            logger.debug("[STABILITY_WORKER] CollisionEvent found", {
              collisionEventId: collisionEvent.id,
              user1Id: collisionEvent.user1Id,
              user2Id: collisionEvent.user2Id,
              status: collisionEvent.status,
              missionId: collisionEvent.missionId,
            });

            // Skip if already has a mission
            if (collisionEvent.missionId) {
              logger.debug("[STABILITY_WORKER] Collision already has mission, skipping", {
                collisionEventId: collisionEvent.id,
                missionId: collisionEvent.missionId,
              });
              await redis.zrem(
                COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
                collisionKey,
              );
              continue;
            }

            // Create mission for this collision
            logger.info("[STABILITY_WORKER] Creating mission for stable collision", {
              circle1Id,
              circle2Id,
              user1Id: collisionEvent.user1Id,
              user2Id: collisionEvent.user2Id,
            });
            const mission = await agentMatchService.createMissionForCollision({
              circle1Id,
              circle2Id,
              user1Id: collisionEvent.user1Id,
              user2Id: collisionEvent.user2Id,
              distance: collisionEvent.distanceMeters,
              timestamp: now,
            });

            if (mission) {
              missionsCreated++;
              logger.info("[STABILITY_WORKER] Mission created successfully", {
                missionId: mission.id,
                circle1Id,
                circle2Id,
              });
            } else {
              logger.warn("[STABILITY_WORKER] Mission creation returned null (likely due to cooldown or lock)", {
                circle1Id,
                circle2Id,
              });
            }

            // Remove from stability queue
            await redis.zrem(
              COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
              collisionKey,
            );
            processedCount++;
          } else {
            logger.debug("[STABILITY_WORKER] Collision not yet stable, skipping", {
              collisionKey,
              stabilityDuration,
              remainingTime: COLLISION_CONFIG.STABILITY_WINDOW_MS - stabilityDuration,
            });
          }
        } catch (error) {
          logger.error("[STABILITY_WORKER] Error processing collision in stability queue", {
            collisionKey,
            error,
          });
        }
      }

      // Step 3: Clean up stale collisions
      await this.cleanupStaleCollisions();

      const tickDuration = Date.now() - tickStartTime;
      logger.info("[STABILITY_WORKER] Tick completed", {
        queueSize: stableCollisions.length,
        processedCount,
        missionsCreated,
        durationMs: tickDuration,
      });
    } catch (error) {
      const tickDuration = Date.now() - tickStartTime;
      logger.error("[STABILITY_WORKER] Tick failed", {
        error,
        durationMs: tickDuration,
      });
    }
  }

  /**
   * Clean up collisions older than 45 seconds
   */
  private async cleanupStaleCollisions(): Promise<void> {
    try {
      const now = Date.now();
      const staleThresholdMs = COLLISION_CONFIG.STALE_COLLISION_THRESHOLD_MS;

      logger.debug("[STABILITY_WORKER] Starting stale collision cleanup", {
        threshold: staleThresholdMs,
        threshold_timestamp: new Date(now - staleThresholdMs).toISOString(),
      });

      // Find and clean up stale collision events
      const staleCollisions = await prisma.collisionEvent.findMany({
        where: {
          firstSeenAt: {
            lt: new Date(now - staleThresholdMs),
          },
          status: {
            in: ["detecting", "stable"],
          },
        },
        select: {
          id: true,
          circle1Id: true,
          circle2Id: true,
          user1Id: true,
          user2Id: true,
          firstSeenAt: true,
        },
      });

      if (staleCollisions.length === 0) {
        logger.debug("[STABILITY_WORKER] No stale collisions to clean up");
        return;
      }

      logger.info("[STABILITY_WORKER] Cleaning up stale collisions", {
        count: staleCollisions.length,
        threshold: staleThresholdMs,
        collisions: staleCollisions.map((c) => ({
          collisionEventId: c.id,
          circle1Id: c.circle1Id,
          circle2Id: c.circle2Id,
          user1Id: c.user1Id,
          user2Id: c.user2Id,
          ageMs: now - c.firstSeenAt.getTime(),
        })),
      });

      const redis = getRedisClient();

      // Delete stale collisions from database
      logger.debug("[STABILITY_WORKER] Updating stale collisions to expired status", {
        count: staleCollisions.length,
      });
      await prisma.collisionEvent.updateMany({
        where: {
          id: {
            in: staleCollisions.map((c: { id: string }) => c.id),
          },
        },
        data: {
          status: "expired",
        },
      });
      logger.debug("[STABILITY_WORKER] Database updated");

      // Clean up Redis keys
      logger.debug("[STABILITY_WORKER] Removing stale collisions from Redis", {
        count: staleCollisions.length,
      });
      for (const collision of staleCollisions) {
        const collisionKey = COLLISION_CONFIG.REDIS_KEYS.collisionActive(
          collision.circle1Id,
          collision.circle2Id,
        );

        logger.debug("[STABILITY_WORKER] Removing Redis key", {
          collisionKey,
          circle1Id: collision.circle1Id,
          circle2Id: collision.circle2Id,
        });

        await redis.del(collisionKey);
        await redis.zrem(
          COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
          `${collision.circle1Id}:${collision.circle2Id}`,
        );
      }
      logger.info("[STABILITY_WORKER] Stale collision cleanup completed", {
        cleanedUpCount: staleCollisions.length,
      });
    } catch (error) {
      logger.error("[STABILITY_WORKER] Failed to cleanup stale collisions", { error });
    }
  }

  /**
   * Gracefully stop the worker
   */
  stop(): void {
    this.isRunning = false;
    logger.info("Stability worker stopped");
  }
}

// Export singleton instance
export const stabilityWorker = new StabilityWorker();
