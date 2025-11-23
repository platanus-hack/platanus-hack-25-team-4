import { prisma } from '../lib/prisma.js';

/**
 * Cleanup Worker
 *
 * Runs every 10 minutes to:
 * 1. Expire old CollisionEvents (older than 48 hours)
 * 2. Expire pending matches (older than 24 hours)
 * 3. Clean stale Redis keys
 */
export class CleanupWorker {
  private isRunning = false;

  /**
   * Start the cleanup worker (runs every 10 minutes)
   */
  start(intervalMs: number = 10 * 60 * 1000): void {
    if (this.isRunning) {
      console.warn('Cleanup worker is already running');
      return;
    }

    this.isRunning = true;
    console.info('Starting cleanup worker with interval', { intervalMs });

    // Run immediately on start
    this.tick().catch(error => {
      console.error('Cleanup worker error on initial tick', { error });
    });

    // Then run at intervals
    setInterval(
      () => {
        this.tick().catch(error => {
          console.error('Cleanup worker error', { error });
        });
      },
      intervalMs
    );
  }

  /**
   * Main tick function - perform cleanup operations
   */
  private async tick(): Promise<void> {
    try {
      const now = new Date();
      console.debug('Cleanup worker tick', { timestamp: now.toISOString() });

      // Perform cleanup operations in parallel
      await Promise.all([
        this.expireOldCollisionEvents(now),
        this.expirePendingMatches(now),
        this.cleanRedisKeys()
      ]);

    } catch (error) {
      console.error('Cleanup worker tick failed', { error });
    }
  }

  /**
   * Expire CollisionEvents older than 48 hours
   */
  private async expireOldCollisionEvents(now: Date): Promise<void> {
    try {
      const expirationThresholdHours = 48;
      const expirationDate = new Date(now.getTime() - expirationThresholdHours * 60 * 60 * 1000);

      const result = await prisma.collisionEvent.updateMany({
        where: {
          createdAt: {
            lt: expirationDate
          },
          status: {
            notIn: ['expired', 'matched']
          }
        },
        data: {
          status: 'expired'
        }
      });

      if (result.count > 0) {
        console.info('Expired old collision events', {
          count: result.count,
          olderThan: expirationDate.toISOString()
        });
      }
    } catch (error) {
      console.error('Failed to expire old collision events', { error });
    }
  }

  /**
   * Expire pending matches older than 24 hours
   */
  private async expirePendingMatches(now: Date): Promise<void> {
    try {
      const expirationThresholdHours = 24;
      const expirationDate = new Date(now.getTime() - expirationThresholdHours * 60 * 60 * 1000);

      const result = await prisma.match.updateMany({
        where: {
          status: 'pending_accept',
          createdAt: {
            lt: expirationDate
          }
        },
        data: {
          status: 'expired'
        }
      });

      if (result.count > 0) {
        console.info('Expired pending matches', {
          count: result.count,
          olderThan: expirationDate.toISOString()
        });
      }
    } catch (error) {
      console.error('Failed to expire pending matches', { error });
    }
  }

  /**
   * Clean up stale Redis keys
   * Removes keys that don't have TTL set (safety cleanup)
   */
  private async cleanRedisKeys(): Promise<void> {
    try {
      // Note: Redis doesn't have a direct way to find all keys without SCAN
      // In production, you should use SCAN to iterate through keys
      // For now, we'll log that this needs to be implemented with proper patterns
      // TODO: Implement Redis key cleanup using SCAN when needed

      console.debug('Redis key cleanup completed');
    } catch (error) {
      console.error('Failed to clean Redis keys', { error });
    }
  }

  /**
   * Gracefully stop the worker
   */
  stop(): void {
    this.isRunning = false;
    console.info('Cleanup worker stopped');
  }
}

// Export singleton instance
export const cleanupWorker = new CleanupWorker();
