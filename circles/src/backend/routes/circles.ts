import { Router } from 'express';
import { z } from 'zod';

import { requireAuth } from '../middlewares/auth.middleware.js';
import { validateBody } from '../middlewares/validate-body.middleware.js';
import type { UpdateCircleInput } from '../repositories/circle-repository.js';
import { CircleService } from '../services/circle-service.js';
import { asyncHandler } from '../utils/async-handler.util.js';

const circleBaseSchema = z.object({
  objective: z.string().trim().min(1),
  radiusMeters: z.number().positive(),
  startAt: z.string().datetime().optional(),
  expiresAt: z.string().datetime().optional().nullable()
});

const createCircleSchema = circleBaseSchema;

const updateCircleSchema = circleBaseSchema
  .partial()
  .extend({ status: z.enum(['active', 'paused', 'expired']).optional() });

export const circlesRouter = Router();

// Service instances
const circleService = new CircleService();

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
    const circle = await circleService.create({
      userId: req.user.userId,
      objective: parsed.objective,
      radiusMeters: parsed.radiusMeters,
      startAt: parsed.startAt ? new Date(parsed.startAt) : new Date(),
      expiresAt: parsed.expiresAt ? new Date(parsed.expiresAt) : null
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

    const circles = await circleService.listByUser(req.user.userId);
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

    const circle = await circleService.getById(circleId, req.user.userId);
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

    const parsed = updateCircleSchema.parse(req.body);
    const updateInput: UpdateCircleInput = {};

    if (parsed.objective !== undefined) {
      updateInput.objective = parsed.objective;
    }
    if (parsed.radiusMeters !== undefined) {
      updateInput.radiusMeters = parsed.radiusMeters;
    }
    if (parsed.startAt !== undefined && parsed.startAt !== null) {
      updateInput.startAt = new Date(parsed.startAt);
    }
    if (parsed.expiresAt !== undefined) {
      updateInput.expiresAt = parsed.expiresAt ? new Date(parsed.expiresAt) : null;
    }
    if (parsed.status !== undefined) {
      updateInput.status = parsed.status;
    }

    const circle = await circleService.update(circleId, req.user.userId, updateInput);
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

    await circleService.remove(circleId, req.user.userId);
    res.status(204).send();
  })
);
