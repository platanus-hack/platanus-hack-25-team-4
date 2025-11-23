import type { Application } from "express";
import jwt from "jsonwebtoken";
import request from "supertest";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { createApp } from "../../app.js";
import { env } from "../../config/env.js";
import { prisma } from "../../lib/prisma.js";

describe("Mission API Endpoints", () => {
  let app: Application;
  let user1Token: string;
  let user2Token: string;
  let user3Token: string;
  let user1Id: string;
  let user2Id: string;
  let user3Id: string;
  let missionId: string;

  beforeAll(async () => {
    app = createApp();

    // Create test users
    const user1 = await prisma.user.create({
      data: {
        email: "mission-user1@test.com",
        passwordHash: "hashed_password",
        firstName: "Mission",
        lastName: "User1",
        centerLat: 40.7128,
        centerLon: -74.006,
      },
    });

    const user2 = await prisma.user.create({
      data: {
        email: "mission-user2@test.com",
        passwordHash: "hashed_password",
        firstName: "Mission",
        lastName: "User2",
        centerLat: 40.7129,
        centerLon: -74.0061,
      },
    });

    const user3 = await prisma.user.create({
      data: {
        email: "mission-user3@test.com",
        passwordHash: "hashed_password",
        firstName: "Mission",
        lastName: "User3",
        centerLat: 40.713,
        centerLon: -74.0062,
      },
    });

    user1Id = user1.id;
    user2Id = user2.id;
    user3Id = user3.id;

    // Generate JWT tokens
    user1Token = jwt.sign(
      { userId: user1.id, email: user1.email },
      env.jwtSecret,
      { expiresIn: "1h" },
    );

    user2Token = jwt.sign(
      { userId: user2.id, email: user2.email },
      env.jwtSecret,
      { expiresIn: "1h" },
    );

    user3Token = jwt.sign(
      { userId: user3.id, email: user3.email },
      env.jwtSecret,
      { expiresIn: "1h" },
    );

    // Create circles for users
    const circle1 = await prisma.circle.create({
      data: {
        userId: user1.id,
        objective: "Test Mission Circle 1",
        radiusMeters: 500,
        status: "active",
        startAt: new Date(),
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days
      },
    });

    const circle2 = await prisma.circle.create({
      data: {
        userId: user2.id,
        objective: "Test Mission Circle 2",
        radiusMeters: 500,
        status: "active",
        startAt: new Date(),
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days
      },
    });

    // Create collision event
    const collision = await prisma.collisionEvent.create({
      data: {
        user1Id: user1.id,
        user2Id: user2.id,
        circle1Id: circle1.id,
        circle2Id: circle2.id,
        distanceMeters: 50,
        status: "stable",
        firstSeenAt: new Date(),
        detectedAt: new Date(),
      },
    });

    // Create mission
    const mission = await prisma.interviewMission.create({
      data: {
        ownerUserId: user1.id,
        visitorUserId: user2.id,
        ownerCircleId: circle1.id,
        visitorCircleId: circle2.id,
        collisionEventId: collision.id,
        status: "pending",
      },
    });

    missionId = mission.id;
  });

  afterAll(async () => {
    // Clean up test data
    await prisma.interviewMission.deleteMany({
      where: {
        OR: [
          { ownerUserId: { in: [user1Id, user2Id, user3Id] } },
          { visitorUserId: { in: [user1Id, user2Id, user3Id] } },
        ],
      },
    });

    await prisma.collisionEvent.deleteMany({
      where: {
        OR: [
          { user1Id: { in: [user1Id, user2Id, user3Id] } },
          { user2Id: { in: [user1Id, user2Id, user3Id] } },
        ],
      },
    });

    await prisma.circle.deleteMany({
      where: { userId: { in: [user1Id, user2Id, user3Id] } },
    });

    await prisma.user.deleteMany({
      where: { id: { in: [user1Id, user2Id, user3Id] } },
    });
  });

  describe("GET /api/missions - Authentication", () => {
    it("should return 401 when no authorization header is provided", async () => {
      const response = await request(app).get("/api/missions").expect(401);

      expect(response.body).toHaveProperty("error");
    });

    it("should return 401 when authorization header is malformed", async () => {
      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", "InvalidFormat")
        .expect(401);

      expect(response.body).toHaveProperty("error");
    });

    it("should return 401 when token is expired", async () => {
      const expiredToken = jwt.sign(
        { userId: user1Id, email: "mission-user1@test.com" },
        env.jwtSecret,
        { expiresIn: "-1h" },
      );

      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${expiredToken}`)
        .expect(401);

      expect(response.body).toHaveProperty("error");
    });

    it("should return 401 when token has invalid signature", async () => {
      const invalidToken = jwt.sign(
        { userId: user1Id, email: "mission-user1@test.com" },
        "wrong_secret",
        { expiresIn: "1h" },
      );

      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${invalidToken}`)
        .expect(401);

      expect(response.body).toHaveProperty("error");
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
      const response = await request(app)
        .get("/api/missions?limit=10000")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.pagination.limit).toBe(100);
    });

    it("should reject negative limit values", async () => {
      const response = await request(app)
        .get("/api/missions?limit=-5")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);

      expect(response.body).toHaveProperty("error");
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
      const response = await request(app)
        .get("/api/missions?offset=-5")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);

      expect(response.body).toHaveProperty("error");
    });

    it("should filter by status parameter", async () => {
      const response = await request(app)
        .get("/api/missions?status=pending")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.missions).toBeInstanceOf(Array);
      response.body.missions.forEach((mission: { status: string }) => {
        expect(mission.status).toBe("pending");
      });
    });

    it("should reject invalid status values", async () => {
      const response = await request(app)
        .get("/api/missions?status=invalid_status")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);

      expect(response.body).toHaveProperty("error");
    });

    it("should filter by startDate parameter", async () => {
      const startDate = new Date(Date.now() - 24 * 60 * 60 * 1000); // 24 hours ago
      const response = await request(app)
        .get(`/api/missions?startDate=${startDate.toISOString()}`)
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.missions).toBeInstanceOf(Array);
      response.body.missions.forEach((mission: { createdAt: string }) => {
        expect(new Date(mission.createdAt).getTime()).toBeGreaterThanOrEqual(
          startDate.getTime(),
        );
      });
    });

    it("should filter by endDate parameter", async () => {
      const endDate = new Date();
      const response = await request(app)
        .get(`/api/missions?endDate=${endDate.toISOString()}`)
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.missions).toBeInstanceOf(Array);
      response.body.missions.forEach((mission: { createdAt: string }) => {
        expect(new Date(mission.createdAt).getTime()).toBeLessThanOrEqual(
          endDate.getTime(),
        );
      });
    });

    it("should apply both startDate and endDate filters", async () => {
      const startDate = new Date(Date.now() - 48 * 60 * 60 * 1000);
      const endDate = new Date();
      const response = await request(app)
        .get(
          `/api/missions?startDate=${startDate.toISOString()}&endDate=${endDate.toISOString()}`,
        )
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.missions).toBeInstanceOf(Array);
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

    it("should set hasMore to false when all results fit in one page", async () => {
      const response = await request(app)
        .get("/api/missions?limit=100")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.pagination.hasMore).toBe(false);
    });

    it("should set hasMore to true when more results exist", async () => {
      const response = await request(app)
        .get("/api/missions?limit=1")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      if (response.body.pagination.total > 1) {
        expect(response.body.pagination.hasMore).toBe(true);
      }
    });

    it("should return empty array when offset exceeds total", async () => {
      const response = await request(app)
        .get("/api/missions?offset=99999")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.missions).toEqual([]);
    });
  });

  describe("GET /api/missions - Authorization", () => {
    it("should only return missions where user is owner or visitor", async () => {
      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.missions).toBeInstanceOf(Array);
      response.body.missions.forEach(
        (mission: { ownerUserId: string; visitorUserId: string }) => {
          expect(
            mission.ownerUserId === user1Id ||
              mission.visitorUserId === user1Id,
          ).toBe(true);
        },
      );
    });

    it("should not return missions where user is neither owner nor visitor", async () => {
      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user3Token}`)
        .expect(200);

      expect(response.body.missions).toBeInstanceOf(Array);
      response.body.missions.forEach(
        (mission: { ownerUserId: string; visitorUserId: string }) => {
          expect(mission.ownerUserId).not.toBe(user1Id);
          expect(mission.ownerUserId).not.toBe(user2Id);
          expect(mission.visitorUserId).not.toBe(user1Id);
          expect(mission.visitorUserId).not.toBe(user2Id);
        },
      );
    });
  });

  describe("GET /api/missions - Data Exposure", () => {
    it("should include expected fields in mission objects", async () => {
      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      if (response.body.missions.length > 0) {
        const mission = response.body.missions[0];
        expect(mission).toHaveProperty("id");
        expect(mission).toHaveProperty("ownerUserId");
        expect(mission).toHaveProperty("visitorUserId");
        expect(mission).toHaveProperty("status");
        expect(mission).toHaveProperty("createdAt");
        expect(mission).toHaveProperty("ownerUser");
        expect(mission).toHaveProperty("visitorUser");
        expect(mission).toHaveProperty("collisionEvent");
      }
    });

    it("should NOT expose password hashes in user objects", async () => {
      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      if (response.body.missions.length > 0) {
        const mission = response.body.missions[0];
        expect(mission.ownerUser.passwordHash).toBeUndefined();
        expect(mission.visitorUser.passwordHash).toBeUndefined();
      }
    });

    it("should include user details in ownerUser", async () => {
      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      if (response.body.missions.length > 0) {
        const mission = response.body.missions[0];
        expect(mission.ownerUser).toHaveProperty("id");
        expect(mission.ownerUser).toHaveProperty("email");
        expect(mission.ownerUser).toHaveProperty("firstName");
        expect(mission.ownerUser).toHaveProperty("lastName");
      }
    });

    it("should include user details in visitorUser", async () => {
      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      if (response.body.missions.length > 0) {
        const mission = response.body.missions[0];
        expect(mission.visitorUser).toHaveProperty("id");
        expect(mission.visitorUser).toHaveProperty("email");
        expect(mission.visitorUser).toHaveProperty("firstName");
        expect(mission.visitorUser).toHaveProperty("lastName");
      }
    });

    it("should include collision event details", async () => {
      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      if (response.body.missions.length > 0) {
        const mission = response.body.missions[0];
        expect(mission.collisionEvent).toHaveProperty("id");
        expect(mission.collisionEvent).toHaveProperty("distanceMeters");
        expect(mission.collisionEvent).toHaveProperty("firstSeenAt");
        expect(mission.collisionEvent).toHaveProperty("status");
        expect(mission.collisionEvent).toHaveProperty("circle1");
        expect(mission.collisionEvent).toHaveProperty("circle2");
      }
    });

    it("should include circle objectives in collision event", async () => {
      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      if (response.body.missions.length > 0) {
        const mission = response.body.missions[0];
        expect(mission.collisionEvent.circle1).toHaveProperty("id");
        expect(mission.collisionEvent.circle1).toHaveProperty("objective");
        expect(mission.collisionEvent.circle1).toHaveProperty("radiusMeters");
        expect(mission.collisionEvent.circle2).toHaveProperty("id");
        expect(mission.collisionEvent.circle2).toHaveProperty("objective");
        expect(mission.collisionEvent.circle2).toHaveProperty("radiusMeters");
      }
    });
  });

  describe("GET /api/missions/:id - Single Mission", () => {
    it("should return mission when user is the owner", async () => {
      const response = await request(app)
        .get(`/api/missions/${missionId}`)
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.mission).toHaveProperty("id", missionId);
      expect(response.body.mission).toHaveProperty("ownerUserId", user1Id);
    });

    it("should return mission when user is the visitor", async () => {
      const response = await request(app)
        .get(`/api/missions/${missionId}`)
        .set("Authorization", `Bearer ${user2Token}`)
        .expect(200);

      expect(response.body.mission).toHaveProperty("id", missionId);
      expect(response.body.mission).toHaveProperty("visitorUserId", user2Id);
    });

    it("should return 403 when user is neither owner nor visitor", async () => {
      const response = await request(app)
        .get(`/api/missions/${missionId}`)
        .set("Authorization", `Bearer ${user3Token}`)
        .expect(403);

      expect(response.body).toHaveProperty("error");
      expect(response.body.error).toContain("Not authorized");
    });

    it("should return 404 when mission does not exist", async () => {
      const response = await request(app)
        .get("/api/missions/non-existent-id")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(404);

      expect(response.body).toHaveProperty("error");
      expect(response.body.error).toContain("Mission not found");
    });

    it("should return 401 when no authorization provided", async () => {
      const response = await request(app)
        .get(`/api/missions/${missionId}`)
        .expect(401);

      expect(response.body).toHaveProperty("error");
    });

    it("should include full user profile in single mission response", async () => {
      const response = await request(app)
        .get(`/api/missions/${missionId}`)
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.mission.ownerUser).toHaveProperty("profile");
      expect(response.body.mission.visitorUser).toHaveProperty("profile");
    });

    it("should include detectedAt in collision event for single mission", async () => {
      const response = await request(app)
        .get(`/api/missions/${missionId}`)
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.mission.collisionEvent).toHaveProperty("detectedAt");
    });

    it("should NOT expose password hashes in single mission response", async () => {
      const response = await request(app)
        .get(`/api/missions/${missionId}`)
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

    it("should handle invalid date formats", async () => {
      const response = await request(app)
        .get("/api/missions?startDate=invalid-date")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);

      expect(response.body).toHaveProperty("error");
    });

    it("should handle missing mission ID parameter", async () => {
      const response = await request(app)
        .get("/api/missions/")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      // This should hit the list endpoint, not the single mission endpoint
      expect(response.body).toHaveProperty("missions");
      expect(response.body).toHaveProperty("pagination");
    });

    it("should sort missions by createdAt descending", async () => {
      const response = await request(app)
        .get("/api/missions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      if (response.body.missions.length > 1) {
        const dates = response.body.missions.map((m: { createdAt: string }) =>
          new Date(m.createdAt).getTime(),
        );
        for (let i = 0; i < dates.length - 1; i++) {
          expect(dates[i]).toBeGreaterThanOrEqual(dates[i + 1]);
        }
      }
    });
  });
});
