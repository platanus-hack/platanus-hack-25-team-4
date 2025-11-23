import { Router, type Request, type Response } from 'express';
import { z } from 'zod';

import { requireAuth } from '../middlewares/auth.middleware.js';
import { validateBody } from '../middlewares/validate-body.middleware.js';
import { LocationService } from '../services/location-service.js';
import { ProfileService } from '../services/profile-service.js';
import { UserService } from '../services/user-service.js';
import { UserProfile } from '../types/user.type.js';
import { asyncHandler } from '../utils/async-handler.util.js';
import { logger } from '../utils/logger.util.js';

const interestSchema = z.object({
  title: z.string().trim().min(1),
  description: z.string().trim().min(1)
});

const profileSchema = z.object({
  bio: z.string().trim().min(1).optional(),
  interests: z.array(interestSchema).optional(),
  profileCompleted: z.boolean().optional(),
  socialStyle: z.string().trim().min(1).optional(),
  boundaries: z.array(z.string().trim().min(1)).optional(),
  availability: z.string().trim().min(1).optional()
});

const updateUserSchema = z.object({
  firstName: z.string().trim().min(1).optional(),
  lastName: z.string().trim().min(1).optional()
});

const updatePositionSchema = z.object({
  centerLat: z.number().min(-90).max(90),
  centerLon: z.number().min(-180).max(180)
});

export const usersRouter = Router();

// Service instances
const userService = new UserService();
const profileService = new ProfileService();
const locationService = new LocationService();

// ============================================================================
// USER CRUD OPERATIONS
// ============================================================================

/**
 * GET /users/me
 * Get current authenticated user
 */
usersRouter.get(
  '/users/me',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const userId = req.user?.userId;
    if (!userId) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const user = await userService.getById(userId);
    if (!user) {
      res.status(404).json({ error: 'User not found' });
      return;
    }

    res.json(user);
  })
);

/**
 * GET /users/:id
 * Get user by ID (public information only)
 */
usersRouter.get(
  '/users/:id',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const { id } = req.params;
    if (typeof id !== 'string') {
      res.status(400).json({ error: 'Invalid user ID' });
      return;
    }

    const user = await userService.getById(id);
    if (!user) {
      res.status(404).json({ error: 'User not found' });
      return;
    }

    res.json(user);
  })
);

/**
 * PATCH /users/me
 * Update current user (firstName, lastName)
 */
usersRouter.patch(
  '/users/me',
  requireAuth,
  validateBody(updateUserSchema),
  asyncHandler(async (req: Request, res: Response) => {
    const userId = req.user?.userId;
    if (!userId) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const parsed = updateUserSchema.parse(req.body);
    // Build update input with only defined values
    const updateInput: Partial<{ firstName: string; lastName: string }> = {};
    if (parsed.firstName !== undefined) {
      updateInput.firstName = parsed.firstName;
    }
    if (parsed.lastName !== undefined) {
      updateInput.lastName = parsed.lastName;
    }
    const user = await userService.update(userId, userId, updateInput);
    res.json(user);
  })
);

/**
 * DELETE /users/me
 * Delete current user account
 */
usersRouter.delete(
  '/users/me',
  requireAuth,
  asyncHandler(async (req: Request, res: Response) => {
    const userId = req.user?.userId;
    if (!userId) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    await userService.delete(userId, userId);
    res.status(204).send();
  })
);

// ============================================================================
// USER POSITION ENDPOINT
// ============================================================================

/**
 * PATCH /users/me/position
 * Update user's current position (latitude and longitude)
 * This is used to center circles at the user's location
 * Triggers collision detection for the new position
 */
usersRouter.patch(
  '/users/me/position',
  requireAuth,
  validateBody(updatePositionSchema),
  asyncHandler(async (req: Request, res: Response) => {
    const userId = req.user?.userId;
    if (!userId) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }
    logger.info("[USERS] Updating user position", {
      userId,
      position: req.body,
    });

    const parsed = updatePositionSchema.parse(req.body);
    const user = await userService.updatePosition(userId, parsed.centerLat, parsed.centerLon);
    
    logger.info("[USERS] User position updated in database", {
      userId,
      newPosition: { centerLat: parsed.centerLat, centerLon: parsed.centerLon }
    });

    // Trigger collision detection for the new position
    // Using accuracy of 0 since this is a manual position update with high confidence
    logger.info("[USERS] Triggering collision detection for position update", {
      userId,
      location: { latitude: parsed.centerLat, longitude: parsed.centerLon }
    });
    
    locationService.updateUserLocation(
      userId,
      parsed.centerLat,
      parsed.centerLon,
      0, // accuracy: 0 for manual position update (high confidence)
      new Date()
    ).catch(error => {
      logger.error('[USERS] Background collision detection failed after position update', error);
      logger.debug('[USERS] Error context', {
        userId,
        position: { centerLat: parsed.centerLat, centerLon: parsed.centerLon }
      });
    });

    res.json({
      message: 'Position updated successfully and collision detection triggered',
      user
    });
  })
);

// ============================================================================
// PROFILE ENDPOINTS (Legacy)
// ============================================================================

usersRouter.get(
  '/users/me/profile',
  requireAuth,
  asyncHandler(async (req, res) => {
    if (!req.user) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const profile = profileService.getProfile(req.user.userId);
    res.json({ profile });
  })
);

usersRouter.put(
  '/users/me/profile',
  requireAuth,
  validateBody(profileSchema),
  asyncHandler(async (req, res) => {
    if (!req.user) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const parsed = profileSchema.parse(req.body);
    const profileInput: UserProfile = {};

    if (parsed.bio !== undefined) {
      profileInput.bio = parsed.bio;
    }
    if (parsed.interests !== undefined) {
      profileInput.interests = parsed.interests;
    }
    if (parsed.profileCompleted !== undefined) {
      profileInput.profileCompleted = parsed.profileCompleted;
    }
    if (parsed.socialStyle !== undefined) {
      profileInput.socialStyle = parsed.socialStyle;
    }
    if (parsed.boundaries !== undefined) {
      profileInput.boundaries = parsed.boundaries;
    }
    if (parsed.availability !== undefined) {
      profileInput.availability = parsed.availability;
    }

    const profile = profileService.updateProfile(req.user.userId, profileInput);
    res.json({ profile });
  })
);
