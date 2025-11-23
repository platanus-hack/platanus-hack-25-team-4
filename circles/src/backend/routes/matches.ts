import { Router } from 'express';
import { z } from 'zod';

import { requireAuth } from '../middlewares/auth.middleware.js';
import { MatchService } from '../services/match-service.js';
import { MatchStatus } from '../types/enums.type.js';
import { asyncHandler } from '../utils/async-handler.util.js';

const queryParamsSchema = z.object({
  status: z.enum(['pending_accept', 'active', 'declined', 'expired']).optional(),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  offset: z.coerce.number().int().min(0).default(0)
});

export const matchesRouter = Router();

// Service instances
const matchService = new MatchService();

/**
 * GET /api/v1/matches
 * List matches for the authenticated user with optional filtering
 */
matchesRouter.get(
  '/matches',
  requireAuth,
  asyncHandler(async (req, res) => {
    if (!req.user) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const { status, limit, offset } = queryParamsSchema.parse(req.query);

    const queryParams: Parameters<typeof matchService.getMatches>[0] = {
      userId: req.user.userId,
      limit,
      offset
    };

    if (status !== undefined) {
      const statusMap: Record<typeof status, MatchStatus> = {
        pending_accept: MatchStatus.PENDING_ACCEPT,
        active: MatchStatus.ACTIVE,
        declined: MatchStatus.DECLINED,
        expired: MatchStatus.EXPIRED
      };
      const mappedStatus = statusMap[status];
      if (mappedStatus !== undefined) {
        queryParams.status = mappedStatus;
      }
    }

    const { matches, total } = await matchService.getMatches(queryParams);

    res.json({
      matches,
      pagination: {
        total,
        limit,
        offset,
        hasMore: offset + limit < total
      }
    });
  })
);

/**
 * GET /api/v1/matches/:id
 * Get a single match by ID
 */
matchesRouter.get(
  '/matches/:id',
  requireAuth,
  asyncHandler(async (req, res) => {
    if (!req.user) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const matchId = req.params.id;
    if (!matchId) {
      res.status(400).json({ error: 'Match ID is required' });
      return;
    }

    const match = await matchService.getMatchById(matchId);

    if (!match) {
      res.status(404).json({ error: 'Match not found' });
      return;
    }

    // Verify user is a participant
    const isParticipant =
      match.primaryUserId === req.user.userId ||
      match.secondaryUserId === req.user.userId;

    if (!isParticipant) {
      res.status(403).json({ error: 'Not authorized to view this match' });
      return;
    }

    res.json({ match });
  })
);

/**
 * POST /api/v1/matches/:id/accept
 * Accept a match and transition to active state
 */
matchesRouter.post(
  '/matches/:id/accept',
  requireAuth,
  asyncHandler(async (req, res) => {
    if (!req.user) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const matchId = req.params.id;
    if (!matchId) {
      res.status(400).json({ error: 'Match ID is required' });
      return;
    }

    const match = await matchService.acceptMatch(matchId, req.user.userId);

    res.json({
      message: 'Match accepted successfully',
      match
    });
  })
);

/**
 * POST /api/v1/matches/:id/decline
 * Decline a match and mark as declined
 */
matchesRouter.post(
  '/matches/:id/decline',
  requireAuth,
  asyncHandler(async (req, res) => {
    if (!req.user) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const matchId = req.params.id;
    if (!matchId) {
      res.status(400).json({ error: 'Match ID is required' });
      return;
    }

    const match = await matchService.declineMatch(matchId, req.user.userId);

    res.json({
      message: 'Match declined successfully',
      match
    });
  })
);
