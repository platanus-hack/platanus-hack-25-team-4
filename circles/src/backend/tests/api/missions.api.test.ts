import type { Application } from "express";
import jwt from "jsonwebtoken";
import request from "supertest";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

import { createApp } from "../../app.js";
import { env } from "../../config/env.js";

// Mock Prisma
vi.mock("../../lib/prisma.js", () => ({
  prisma: {
    interviewMission: {
      findMany: vi.fn(),
      findUnique: vi.fn(),
      count: vi.fn(),
    },
  },
}));

import { prisma } from "../../lib/prisma.js";

describe("Mission API Endpoints", () => {
  let app: Application;
  let user1Token: string;
  let user2Token: string;
  let user3Token: string;
  const user1Id = "test-user-1";
  const user2Id = "test-user-2";
  const user3Id = "test-user-3";

  const mockMission = {
    id: "mission-1",
    ownerUserId: user1Id,
    visitorUserId: user2Id,
    ownerCircleId: "circle-1",
    visitorCircleId: "circle-2",
    collisionEventId: "collision-1",
    status: "pending",
    transcript: null,
    judgeDecision: null,
    createdAt: new Date(),
    completedAt: null,
    startedAt: null,
    failureReason: null,
    attemptNumber: 1,
    ownerUser: {
      id: user1Id,
      email: "user1@test.com",
      firstName: "Owner",
      lastName: "User",
    },
    visitorUser: {
      id: user2Id,
      email: "user2@test.com",
      firstName: "Visitor",
      lastName: "User",
    },
    collisionEvent: {
      id: "collision-1",
      distanceMeters: 100,
      firstSeenAt: new Date(),
      status: "stable",
      circle1: {
        id: "circle-1",
        objective: "Test Objective 1",
        radiusMeters: 500,
      },
      circle2: {
        id: "circle-2",
        objective: "Test Objective 2",
        radiusMeters: 500,
      },
    },
  };

  beforeAll(() => {
    app = createApp();

    // Generate JWT tokens
    user1Token = jwt.sign(
      { userId: user1Id, email: "user1@test.com" },
      env.jwtSecret,
      { expiresIn: "1h" },
    );

    user2Token = jwt.sign(
      { userId: user2Id, email: "user2@test.com" },
      env.jwtSecret,
      { expiresIn: "1h" },
    );

    user3Token = jwt.sign(
      { userId: user3Id, email: "user3@test.com" },
      env.jwtSecret,
      { expiresIn: "1h" },
    );
  });

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(prisma.interviewMission.findMany).mockResolvedValue([]);
    vi.mocked(prisma.interviewMission.count).mockResolvedValue(0);
    vi.mocked(prisma.interviewMission.findUnique).mockResolvedValue(null);
  });

  describe("GET /api/missions - Authentication", () => {
    it("should return 401 when no authorization header is provided", async () => {
      await request(app).get("/api/missions").expect(401);
    });

    it("should return 401 when authorization header is malformed", async () => {
      await request(app)
        .get("/api/missions")
        .set("Authorization", "InvalidFormat")
        .expect(401);
    });

    it("should return 401 when token is expired", async () => {
      const expiredToken = jwt.sign(
        { userId: user1Id, email: "user1@test.com" },
        env.jwtSecret,
        { expiresIn: "-1h" },
      );

      await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${expiredToken}`)
        .expect(401);
    });

    it("should return 401 when token has invalid signature", async () => {
      const invalidToken = jwt.sign(
        { userId: user1Id, email: "user1@test.com" },
        "wrong_secret",
        { expiresIn: "1h" },
      );

      await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${invalidToken}`)
        .expect(401);
    });

    it("should return 200 when valid token is provided", async () => {
      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body).toHaveProperty("missions");
      expect(response.body).toHaveProperty("pagination");
    });
  });

  describe("GET /api/missions - Query Parameters", () => {
    it("should apply default limit of 20 when not specified", async () => {
      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.pagination.limit).toBe(20);
    });

    it("should respect custom limit parameter", async () => {
      const response = await request(app)
        .get("/api/missions?limit=5")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.pagination.limit).toBe(5);
    });

    it("should enforce maximum limit of 100", async () => {
      await request(app)
        .get("/api/missions?limit=10000")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);
    });

    it("should reject negative limit values", async () => {
      await request(app)
        .get("/api/missions?limit=-5")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);
    });

    it("should apply default offset of 0 when not specified", async () => {
      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.pagination.offset).toBe(0);
    });

    it("should respect custom offset parameter", async () => {
      const response = await request(app)
        .get("/api/missions?offset=10")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.pagination.offset).toBe(10);
    });

    it("should reject negative offset values", async () => {
      await request(app)
        .get("/api/missions?offset=-5")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);
    });

    it("should filter by status parameter", async () => {
      vi.mocked(prisma.interviewMission.findMany).mockResolvedValue([
        mockMission,
      ]);
      vi.mocked(prisma.interviewMission.count).mockResolvedValue(1);

      const response = await request(app)
        .get("/api/missions?status=pending")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.missions).toBeInstanceOf(Array);
    });

    it("should reject invalid status values", async () => {
      await request(app)
        .get("/api/missions?status=invalid_status")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);
    });

    it("should handle invalid date formats", async () => {
      await request(app)
        .get("/api/missions?startDate=invalid-date")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);
    });
  });

  describe("GET /api/missions - Pagination", () => {
    it("should include pagination metadata in response", async () => {
      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.pagination).toHaveProperty("total");
      expect(response.body.pagination).toHaveProperty("limit");
      expect(response.body.pagination).toHaveProperty("offset");
      expect(response.body.pagination).toHaveProperty("hasMore");
    });

    it("should set hasMore correctly when more results exist", async () => {
      vi.mocked(prisma.interviewMission.count).mockResolvedValue(25);

      const response = await request(app)
        .get("/api/missions?limit=20")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.pagination.hasMore).toBe(true);
    });

    it("should return empty array when offset exceeds total", async () => {
      vi.mocked(prisma.interviewMission.count).mockResolvedValue(5);

      const response = await request(app)
        .get("/api/missions?offset=99999")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.missions).toEqual([]);
    });
  });

  describe("GET /api/missions - Authorization", () => {
    it("should only return missions where user is owner or visitor", async () => {
      vi.mocked(prisma.interviewMission.findMany).mockResolvedValue([
        mockMission,
      ]);

      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      // Verify WHERE clause was built correctly
      expect(prisma.interviewMission.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            OR: [{ ownerUserId: user1Id }, { visitorUserId: user1Id }],
          }),
        }),
      );
    });

    it("should not return missions where user is neither owner nor visitor", async () => {
      vi.mocked(prisma.interviewMission.findMany).mockResolvedValue([]);

      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user3Token}`)
        .expect(200);

      expect(response.body.missions).toEqual([]);
    });
  });

  describe("GET /api/missions - Data Exposure", () => {
    it("should include expected fields in mission objects", async () => {
      vi.mocked(prisma.interviewMission.findMany).mockResolvedValue([
        mockMission,
      ]);

      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      const mission = response.body.missions[0];
      expect(mission).toHaveProperty("id");
      expect(mission).toHaveProperty("ownerUserId");
      expect(mission).toHaveProperty("visitorUserId");
      expect(mission).toHaveProperty("status");
      expect(mission).toHaveProperty("createdAt");
    });

    it("should NOT expose password hashes in user objects", async () => {
      vi.mocked(prisma.interviewMission.findMany).mockResolvedValue([
        mockMission,
      ]);

      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      const mission = response.body.missions[0];
      expect(mission.ownerUser.passwordHash).toBeUndefined();
      expect(mission.visitorUser.passwordHash).toBeUndefined();
    });

    it("should include collision event details", async () => {
      vi.mocked(prisma.interviewMission.findMany).mockResolvedValue([
        mockMission,
      ]);

      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      const mission = response.body.missions[0];
      expect(mission.collisionEvent).toHaveProperty("id");
      expect(mission.collisionEvent).toHaveProperty("distanceMeters");
      expect(mission.collisionEvent).toHaveProperty("circle1");
      expect(mission.collisionEvent).toHaveProperty("circle2");
    });
  });

  describe("GET /api/missions/:id - Single Mission", () => {
    it("should return mission when user is the owner", async () => {
      vi.mocked(prisma.interviewMission.findUnique).mockResolvedValue({
        ...mockMission,
        ownerUser: { ...mockMission.ownerUser, profile: null },
        visitorUser: { ...mockMission.visitorUser, profile: null },
        collisionEvent: { ...mockMission.collisionEvent, detectedAt: new Date() },
      });

      const response = await request(app)
        .get("/api/missions/mission-1")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.mission.id).toBe("mission-1");
    });

    it("should return mission when user is the visitor", async () => {
      vi.mocked(prisma.interviewMission.findUnique).mockResolvedValue({
        ...mockMission,
        ownerUser: { ...mockMission.ownerUser, profile: null },
        visitorUser: { ...mockMission.visitorUser, profile: null },
        collisionEvent: { ...mockMission.collisionEvent, detectedAt: new Date() },
      });

      const response = await request(app)
        .get("/api/missions/mission-1")
        .set("Authorization", `Bearer ${user2Token}`)
        .expect(200);

      expect(response.body.mission.id).toBe("mission-1");
    });

    it("should return 403 when user is neither owner nor visitor", async () => {
      vi.mocked(prisma.interviewMission.findUnique).mockResolvedValue({
        ...mockMission,
        ownerUser: { ...mockMission.ownerUser, profile: null },
        visitorUser: { ...mockMission.visitorUser, profile: null },
        collisionEvent: { ...mockMission.collisionEvent, detectedAt: new Date() },
      });

      await request(app)
        .get("/api/missions/mission-1")
        .set("Authorization", `Bearer ${user3Token}`)
        .expect(403);
    });

    it("should return 404 when mission does not exist", async () => {
      vi.mocked(prisma.interviewMission.findUnique).mockResolvedValue(null);

      await request(app)
        .get("/api/missions/non-existent-id")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(404);
    });

    it("should return 401 when no authorization provided", async () => {
      await request(app).get("/api/missions/mission-1").expect(401);
    });

    it("should NOT expose password hashes in single mission response", async () => {
      vi.mocked(prisma.interviewMission.findUnique).mockResolvedValue({
        ...mockMission,
        ownerUser: { ...mockMission.ownerUser, profile: null },
        visitorUser: { ...mockMission.visitorUser, profile: null },
        collisionEvent: { ...mockMission.collisionEvent, detectedAt: new Date() },
      });

      const response = await request(app)
        .get("/api/missions/mission-1")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.mission.ownerUser.passwordHash).toBeUndefined();
      expect(response.body.mission.visitorUser.passwordHash).toBeUndefined();
    });
  });

  describe("GET /api/missions - Edge Cases", () => {
    it("should handle empty results gracefully", async () => {
      const response = await request(app)
        .get("/api/missions?status=failed")
        .set("Authorization", `Bearer ${user3Token}`)
        .expect(200);

      expect(response.body.missions).toEqual([]);
      expect(response.body.pagination.total).toBe(0);
    });

    it("should sort missions by createdAt descending", async () => {
      const mission1 = { ...mockMission, id: "m1", createdAt: new Date("2024-01-02") };
      const mission2 = { ...mockMission, id: "m2", createdAt: new Date("2024-01-01") };

      vi.mocked(prisma.interviewMission.findMany).mockResolvedValue([
        mission1,
        mission2,
      ]);

      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      // Verify orderBy was called with createdAt desc
      expect(prisma.interviewMission.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          orderBy: { createdAt: "desc" },
        }),
      );
    });
  });
});
