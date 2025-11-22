import { Router } from 'express';
import { z } from 'zod';

import { requireAuth } from '../middlewares/auth.middleware.js';
import { validateBody } from '../middlewares/validate-body.middleware.js';
import type { UpdateCircleInput } from '../repositories/circle-repository.js';
import { circleService } from '../services/circle-service.js';
import { asyncHandler } from '../utils/async-handler.util.js';

const circleBaseSchema = z.object({
  objectiveText: z.string().trim().min(1),
  centerLat: z.number(),
  centerLon: z.number(),
  radiusMeters: z.number().positive(),
  startAt: z.string().datetime(),
  expiresAt: z.string().datetime()
});

const createCircleSchema = circleBaseSchema;

const updateCircleSchema = circleBaseSchema
  .partial()
  .extend({ status: z.enum(['active', 'paused', 'expired']).optional() });

export const circlesRouter = Router();

circlesRouter.post(
  '/circles',
  requireAuth,
  validateBody(createCircleSchema),
  asyncHandler(async (req, res) => {
    if (!req.user) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const parsed = createCircleSchema.parse(req.body);
    const circle = circleService.create({
      userId: req.user.userId,
      objective: parsed.objectiveText,
      centerLat: parsed.centerLat,
      centerLon: parsed.centerLon,
      radiusMeters: parsed.radiusMeters,
      startAt: new Date(parsed.startAt),
      expiresAt: new Date(parsed.expiresAt)
    });
    res.status(201).json({ circle });
  })
);

circlesRouter.get(
  '/circles/me',
  requireAuth,
  asyncHandler(async (req, res) => {
    if (!req.user) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const circles = circleService.listByUser(req.user.userId);
    res.json({ circles });
  })
);

circlesRouter.get(
  '/circles/:id',
  requireAuth,
  asyncHandler(async (req, res) => {
    if (!req.user) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const circleId = req.params.id;
    if (!circleId) {
      res.status(400).json({ error: 'Circle id is required' });
      return;
    }

    const circle = circleService.getById(circleId, req.user.userId);
    res.json({ circle });
  })
);

circlesRouter.patch(
  '/circles/:id',
  requireAuth,
  validateBody(updateCircleSchema),
  asyncHandler(async (req, res) => {
    if (!req.user) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const circleId = req.params.id;
    if (!circleId) {
      res.status(400).json({ error: 'Circle id is required' });
      return;
    }

    const parsed = circleBaseSchema.parse(req.body);
    const updateInput: UpdateCircleInput = {};

    if (parsed.objectiveText !== undefined) {
      updateInput.objective = parsed.objectiveText;
    }
    if (parsed.centerLat !== undefined) {
      updateInput.centerLat = parsed.centerLat;
    }
    if (parsed.centerLon !== undefined) {
      updateInput.centerLon = parsed.centerLon;
    }
    if (parsed.radiusMeters !== undefined) {
      updateInput.radiusMeters = parsed.radiusMeters;
    }
    if (parsed.startAt !== undefined) {
      updateInput.startAt = new Date(parsed.startAt);
    }
    if (parsed.expiresAt !== undefined) {
      updateInput.expiresAt = new Date(parsed.expiresAt);
    }

    const circle = circleService.update(circleId, req.user.userId, updateInput);
    res.json({ circle });
  })
);

circlesRouter.delete(
  '/circles/:id',
  requireAuth,
  asyncHandler(async (req, res) => {
    if (!req.user) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const circleId = req.params.id;
    if (!circleId) {
      res.status(400).json({ error: 'Circle id is required' });
      return;
    }

    circleService.remove(circleId, req.user.userId);
    res.status(204).send();
  })
);
