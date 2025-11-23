import { Router } from 'express';
import { z } from 'zod';

import { requireAuth } from '../middlewares/auth.middleware.js';
import { validateBody } from '../middlewares/validate-body.middleware.js';
import { LocationService } from '../services/location-service.js';
import { asyncHandler } from '../utils/async-handler.util.js';
import { logger } from '../utils/logger.util.js';

const updateLocationSchema = z.object({
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
  accuracy: z.number().positive().optional().default(0),
  timestamp: z.string().datetime().optional()
});

export const locationsRouter = Router();

// Service instances
const locationService = new LocationService();

// Rate limiting map for location updates (1 per user per 10 seconds)
const lastLocationUpdate = new Map<string, number>();

/**
 * Check rate limit: 1 update per 10 seconds per user
 */
function checkRateLimit(userId: string): boolean {
  const lastUpdate = lastLocationUpdate.get(userId);
  const now = Date.now();

  if (!lastUpdate || now - lastUpdate >= 10000) {
    lastLocationUpdate.set(userId, now);
    logger.debug("[COLLISION_PIPELINE] Rate limit: Update allowed", { userId });
    return true;
  }

  const timeSinceLastUpdate = now - lastUpdate;
  logger.debug("[COLLISION_PIPELINE] Rate limit: Update rate limited", {
    userId,
    timeSinceLastUpdate,
    maxAllowed: 10000,
  });
  return false;
}

/**
 * POST /api/v1/locations/update
 * Update user location and trigger collision detection
 * Returns 202 Accepted (async processing)
 */
locationsRouter.post(
  '/locations/update',
  requireAuth,
  validateBody(updateLocationSchema),
  asyncHandler(async (req, res) => {
    if (!req.user) {
      logger.warn("[COLLISION_PIPELINE] Location endpoint: Unauthorized request");
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const userId = req.user.userId;
    logger.info("[COLLISION_PIPELINE] Location endpoint: Request received", {
      userId,
      body: req.body,
    });

    // Check rate limit
    if (!checkRateLimit(userId)) {
      logger.warn("[COLLISION_PIPELINE] Location endpoint: Rate limited", {
        userId,
      });
      res.status(429).json({
        error: 'Too many location updates. Maximum 1 per 10 seconds.'
      });
      return;
    }

    const { latitude, longitude, accuracy, timestamp } = updateLocationSchema.parse(req.body);

    logger.info("[COLLISION_PIPELINE] Location endpoint: Starting async processing", {
      userId,
      location: { latitude, longitude, accuracy },
      timestamp,
    });

    // Process location update asynchronously
    await locationService.updateUserLocation(
      userId,
      latitude,
      longitude,
      accuracy,
      timestamp ? new Date(timestamp) : new Date()
    ).catch(error => {
      logger.error('[COLLISION_PIPELINE] Background location processing failed', {
        userId,
        error
      });
    });

    // Return 202 Accepted immediately
    res.status(202).json({
      message: 'Location update accepted and being processed',
      location: { latitude, longitude, accuracy }
    });
  })
);
