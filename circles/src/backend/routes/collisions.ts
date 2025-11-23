import { Prisma } from "@prisma/client";
import { Router } from "express";
import { z } from "zod";

import { prisma } from "../lib/prisma.js";
import { requireAuth } from "../middlewares/auth.middleware.js";
import { asyncHandler } from "../utils/async-handler.util.js";

const queryParamsSchema = z.object({
  status: z.enum(["detecting", "stable", "expired"]).optional(),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  offset: z.coerce.number().int().min(0).default(0),
  startDate: z.coerce.date().optional(),
  endDate: z.coerce.date().optional(),
});

export const collisionsRouter = Router();

/**
 * GET /api/v1/collisions
 * List collision events for the authenticated user with optional filtering
 */
collisionsRouter.get(
  "/collisions",
  requireAuth,
  asyncHandler(async (req, res) => {
    if (!req.user) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    const { status, limit, offset, startDate, endDate } =
      queryParamsSchema.parse(req.query);

    // Build where clause
    const where: Prisma.CollisionEventWhereInput = {
      OR: [{ user1Id: req.user.userId }, { user2Id: req.user.userId }],
    };

    if (status !== undefined) {
      where.status = status;
    }

    if (startDate || endDate) {
      where.firstSeenAt = {};
      if (startDate) {
        where.firstSeenAt.gte = startDate;
      }
      if (endDate) {
        where.firstSeenAt.lte = endDate;
      }
    }

    // Execute queries in parallel
    const [collisions, total] = await Promise.all([
      prisma.collisionEvent.findMany({
        where,
        orderBy: { firstSeenAt: "desc" },
        skip: offset,
        take: limit,
        include: {
          circle1: {
            select: {
              id: true,
              objective: true,
              radiusMeters: true,
              userId: true,
            },
          },
          circle2: {
            select: {
              id: true,
              objective: true,
              radiusMeters: true,
              userId: true,
            },
          },
          user1: {
            select: {
              id: true,
              email: true,
              firstName: true,
              lastName: true,
            },
          },
          user2: {
            select: {
              id: true,
              email: true,
              firstName: true,
              lastName: true,
            },
          },
          mission: {
            select: {
              id: true,
              status: true,
              createdAt: true,
            },
          },
        },
      }),
      prisma.collisionEvent.count({ where }),
    ]);

    res.json({
      collisions,
      pagination: {
        total,
        limit,
        offset,
        hasMore: offset + limit < total,
      },
    });
  }),
);

/**
 * GET /api/v1/collisions/:id
 * Get a single collision event by ID
 */
collisionsRouter.get(
  "/collisions/:id",
  requireAuth,
  asyncHandler(async (req, res) => {
    if (!req.user) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    const collisionId = req.params.id;
    if (!collisionId) {
      res.status(400).json({ error: "Collision ID is required" });
      return;
    }

    const collision = await prisma.collisionEvent.findUnique({
      where: { id: collisionId },
      include: {
        circle1: {
          select: {
            id: true,
            objective: true,
            radiusMeters: true,
            userId: true,
          },
        },
        circle2: {
          select: {
            id: true,
            objective: true,
            radiusMeters: true,
            userId: true,
          },
        },
        user1: {
          select: {
            id: true,
            email: true,
            firstName: true,
            lastName: true,
          },
        },
        user2: {
          select: {
            id: true,
            email: true,
            firstName: true,
            lastName: true,
          },
        },
        mission: {
          select: {
            id: true,
            status: true,
            createdAt: true,
            completedAt: true,
          },
        },
        match: {
          select: {
            id: true,
            status: true,
            createdAt: true,
          },
        },
      },
    });

    if (!collision) {
      res.status(404).json({ error: "Collision not found" });
      return;
    }

    // Verify user is a participant
    const isParticipant =
      collision.user1Id === req.user.userId ||
      collision.user2Id === req.user.userId;

    if (!isParticipant) {
      res.status(403).json({ error: "Not authorized to view this collision" });
      return;
    }

    res.json({ collision });
  }),
);
