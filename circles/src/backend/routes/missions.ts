import { Prisma } from "@prisma/client";
import { Router } from "express";
import { z } from "zod";

import { prisma } from "../lib/prisma.js";
import { requireAuth } from "../middlewares/auth.middleware.js";
import { asyncHandler } from "../utils/async-handler.util.js";

const queryParamsSchema = z.object({
  status: z.enum(["pending", "in_progress", "completed", "failed"]).optional(),
  type: z.enum(["circle_collision"]).optional(),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  offset: z.coerce.number().int().min(0).default(0),
  startDate: z.coerce.date().optional(),
  endDate: z.coerce.date().optional(),
});

export const missionsRouter = Router();

/**
 * GET /api/v1/missions
 * List interview missions for the authenticated user with optional filtering
 */
missionsRouter.get(
  "/missions",
  requireAuth,
  asyncHandler(async (req, res) => {
    if (!req.user) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    // Validate query parameters
    const parseResult = queryParamsSchema.safeParse(req.query);
    if (!parseResult.success) {
      res.status(400).json({ error: parseResult.error.errors });
      return;
    }

    const { status, limit, offset, startDate, endDate } = parseResult.data;

    // Build where clause
    const where: Prisma.InterviewMissionWhereInput = {
      OR: [
        { ownerUserId: req.user.userId },
        { visitorUserId: req.user.userId },
      ],
    };

    if (status !== undefined) {
      where.status = status;
    }

    // Note: type filtering removed - InterviewMission schema doesn't have a type field
    // All missions in this table are circle_collision type by design

    if (startDate || endDate) {
      where.createdAt = {};
      if (startDate) {
        where.createdAt.gte = startDate;
      }
      if (endDate) {
        where.createdAt.lte = endDate;
      }
    }

    // Execute queries in parallel
    const [missions, total] = await Promise.all([
      prisma.interviewMission.findMany({
        where,
        orderBy: { createdAt: "desc" },
        skip: offset,
        take: limit,
        include: {
          ownerUser: {
            select: {
              id: true,
              email: true,
              firstName: true,
              lastName: true,
            },
          },
          visitorUser: {
            select: {
              id: true,
              email: true,
              firstName: true,
              lastName: true,
            },
          },
          collisionEvent: {
            select: {
              id: true,
              distanceMeters: true,
              firstSeenAt: true,
              status: true,
              circle1: {
                select: {
                  id: true,
                  objective: true,
                  radiusMeters: true,
                },
              },
              circle2: {
                select: {
                  id: true,
                  objective: true,
                  radiusMeters: true,
                },
              },
            },
          },
        },
      }),
      prisma.interviewMission.count({ where }),
    ]);

    res.json({
      missions,
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
 * GET /api/v1/missions/:id
 * Get a single mission by ID with full interview state
 */
missionsRouter.get(
  "/missions/:id",
  requireAuth,
  asyncHandler(async (req, res) => {
    if (!req.user) {
      res.status(401).json({ error: "Unauthorized" });
      return;
    }

    const missionId = req.params.id;
    if (!missionId) {
      res.status(400).json({ error: "Mission ID is required" });
      return;
    }

    const mission = await prisma.interviewMission.findUnique({
      where: { id: missionId },
      include: {
        ownerUser: {
          select: {
            id: true,
            email: true,
            firstName: true,
            lastName: true,
            profile: true,
          },
        },
        visitorUser: {
          select: {
            id: true,
            email: true,
            firstName: true,
            lastName: true,
            profile: true,
          },
        },
        collisionEvent: {
          select: {
            id: true,
            distanceMeters: true,
            firstSeenAt: true,
            detectedAt: true,
            status: true,
            circle1: {
              select: {
                id: true,
                objective: true,
                radiusMeters: true,
              },
            },
            circle2: {
              select: {
                id: true,
                objective: true,
                radiusMeters: true,
              },
            },
          },
        },
      },
    });

    if (!mission) {
      res.status(404).json({ error: "Mission not found" });
      return;
    }

    // Verify user is a participant
    const isParticipant =
      mission.ownerUserId === req.user.userId ||
      mission.visitorUserId === req.user.userId;

    if (!isParticipant) {
      res.status(403).json({ error: "Not authorized to view this mission" });
      return;
    }

    res.json({ mission });
  }),
);
