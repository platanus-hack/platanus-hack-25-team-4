import { Router, Request, Response } from 'express';

import { env } from '../config/env.js';
import { getEventBus } from '../infrastructure/observer/index.js';
import { getRedisClient } from '../infrastructure/redis.js';

export const healthRouter = Router();

healthRouter.get('/health', (_req: Request, res: Response) => {
  void (async () => {
  try {
    // Check Redis connectivity
    let redisHealthy = false;
    let redisError = null;
    try {
      const redis = getRedisClient();
      await redis.ping();
      redisHealthy = true;
    } catch (error) {
      redisError = error instanceof Error ? error.message : 'Unknown error';
    }

    // Get observer status
    const eventBus = getEventBus();
    const circuitStats = eventBus.getCircuitStats();
    const bufferSize = eventBus.getBufferSize();

    const observerHealthy = circuitStats.state !== 'open';
    const overallStatus =
      redisHealthy && observerHealthy ? 'healthy' : 'degraded';

    const statusCode = redisHealthy ? 200 : 503;

    res.status(statusCode).json({
      status: overallStatus,
      timestamp: Date.now(),
      redis: {
        connected: redisHealthy,
        error: redisError,
      },
      observer: {
        enabled: env.observerEnabled,
        circuitState: circuitStats.state,
        bufferSize,
        failureCount: circuitStats.failureCount,
        successCount: circuitStats.successCount,
      },
    });
  } catch (error) {
    console.error('[Health Check] Failed', { error });
    res.status(500).json({
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
  })();
});
