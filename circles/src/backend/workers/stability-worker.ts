import { COLLISION_CONFIG } from '../config/collision.config.js';
import { getRedisClient } from '../infrastructure/redis.js';
import { prisma } from '../lib/prisma.js';
import { AgentMatchService } from '../services/agent-match-service.js';

/**
 * Stability Queue Worker
 *
 * Runs every 5 seconds to:
 * 1. Process stability queue - promote collisions that have been stable for 30s
 * 2. Create missions for promoted collisions
 * 3. Clean up stale collisions older than 45s
 */
export class StabilityWorker {
  private agentMatchService: AgentMatchService;
  private isRunning = false;

  constructor() {
    this.agentMatchService = new AgentMatchService();
  }

  /**
   * Start the stability worker (runs every 5 seconds)
   */
  start(intervalMs: number = 5000): void {
    if (this.isRunning) {
      console.warn('Stability worker is already running');
      return;
    }

    this.isRunning = true;
    console.info('Starting stability worker with interval', { intervalMs });

    // Run immediately on start
    this.tick().catch(error => {
      console.error('Stability worker error on initial tick', { error });
    });

    // Then run at intervals
    setInterval(
      () => {
        this.tick().catch(error => {
          console.error('Stability worker error', { error });
        });
      },
      intervalMs
    );
  }

  /**
   * Main tick function - process stability queue and cleanup
   */
  private async tick(): Promise<void> {
    try {
      const redis = getRedisClient();
      const now = Date.now();

      // Step 1: Get collisions from stability queue
      const stableCollisions = await redis.zrange(
        COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
        0,
        -1
      );

      console.debug('Stability worker tick', {
        stableCollisions: stableCollisions.length,
        timestamp: new Date(now).toISOString()
      });

      // Step 2: Process each stable collision
      for (const collisionKey of stableCollisions) {
        try {
          // Get collision details from Redis
          const collisionData = await redis.hgetall(
            COLLISION_CONFIG.REDIS_KEYS.collisionActive(
              collisionKey.split(':')[0]!,
              collisionKey.split(':')[1]!
            )
          );

          if (!collisionData || Object.keys(collisionData).length === 0) {
            // Collision data expired, remove from queue
            await redis.zrem(
              COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
              collisionKey
            );
            continue;
          }

          const firstSeenAt = parseInt(collisionData.firstSeenAt || '0');
          const stabilityDuration = now - firstSeenAt;

          // Check if collision has been stable for 30 seconds
          if (stabilityDuration >= COLLISION_CONFIG.STABILITY_WINDOW_MS) {
            // Promote collision to mission creation
            const circle1Id = collisionData.circle1Id;
            const circle2Id = collisionData.circle2Id;

            if (!circle1Id || !circle2Id) {
              console.warn('Missing circle IDs in collision data', { collisionData });
              await redis.zrem(
                COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
                collisionKey
              );
              continue;
            }

            // Get collision event from database
            const collisionEvent = await prisma.collisionEvent.findUnique({
              where: {
                unique_collision_pair: { circle1Id, circle2Id }
              }
            });

            if (!collisionEvent) {
              console.warn('Collision event not found in database', {
                circle1Id,
                circle2Id
              });
              await redis.zrem(
                COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
                collisionKey
              );
              continue;
            }

            // Create mission for this collision
            const mission = await this.agentMatchService.createMissionForCollision({
              circle1Id,
              circle2Id,
              user1Id: collisionEvent.user1Id,
              user2Id: collisionEvent.user2Id,
              distance: collisionEvent.distanceMeters,
              timestamp: now
            });

            if (mission) {
              console.info('Mission created from stable collision', {
                missionId: mission.id,
                circle1Id,
                circle2Id
              });
            }

            // Remove from stability queue
            await redis.zrem(
              COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
              collisionKey
            );
          }
        } catch (error) {
          console.error('Error processing collision in stability queue', {
            collisionKey,
            error
          });
        }
      }

      // Step 3: Clean up stale collisions
      await this.cleanupStaleCollisions();

    } catch (error) {
      console.error('Stability worker tick failed', { error });
    }
  }

  /**
   * Clean up collisions older than 45 seconds
   */
  private async cleanupStaleCollisions(): Promise<void> {
    try {
      const now = Date.now();
      const staleThresholdMs = COLLISION_CONFIG.STALE_COLLISION_THRESHOLD_MS;

      // Find and clean up stale collision events
      const staleCollisions = await prisma.collisionEvent.findMany({
        where: {
          firstSeenAt: {
            lt: new Date(now - staleThresholdMs)
          },
          status: {
            in: ['detecting', 'stable']
          }
        },
        select: {
          id: true,
          circle1Id: true,
          circle2Id: true
        }
      });

      if (staleCollisions.length === 0) {
        return;
      }

      console.info('Cleaning up stale collisions', {
        count: staleCollisions.length,
        threshold: staleThresholdMs
      });

      const redis = getRedisClient();

      // Delete stale collisions from database
      await prisma.collisionEvent.updateMany({
        where: {
          id: {
            in: staleCollisions.map((c: { id: string }) => c.id)
          }
        },
        data: {
          status: 'expired'
        }
      });

      // Clean up Redis keys
      for (const collision of staleCollisions) {
        const collisionKey = COLLISION_CONFIG.REDIS_KEYS.collisionActive(
          collision.circle1Id,
          collision.circle2Id
        );

        await redis.del(collisionKey);
        await redis.zrem(
          COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
          `${collision.circle1Id}:${collision.circle2Id}`
        );
      }

    } catch (error) {
      console.error('Failed to cleanup stale collisions', { error });
    }
  }

  /**
   * Gracefully stop the worker
   */
  stop(): void {
    this.isRunning = false;
    console.info('Stability worker stopped');
  }
}

// Export singleton instance
export const stabilityWorker = new StabilityWorker();
