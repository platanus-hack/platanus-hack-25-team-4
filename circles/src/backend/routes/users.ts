import { Router } from 'express';
import { z } from 'zod';

import { requireAuth } from '../middlewares/auth.middleware.js';
import { validateBody } from '../middlewares/validate-body.middleware.js';
import { profileService } from '../services/profile-service.js';
import { UserProfile } from '../types/user.type.js';
import { asyncHandler } from '../utils/async-handler.util.js';

const profileSchema = z.object({
  interests: z.array(z.string().trim().min(1)).default([]),
  socialStyle: z.string().trim().min(1).optional(),
  boundaries: z.array(z.string().trim().min(1)).optional(),
  availability: z.string().trim().min(1).optional()
});

export const usersRouter = Router();

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
    const profileInput: UserProfile = { interests: parsed.interests };
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
