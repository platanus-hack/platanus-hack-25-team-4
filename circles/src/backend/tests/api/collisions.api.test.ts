import type { Application } from "express";
import jwt from "jsonwebtoken";
import request from "supertest";
import { afterAll, beforeAll, beforeEach, describe, expect, it } from "vitest";

import { createApp } from "../../app.js";
import { env } from "../../config/env.js";
import { prisma } from "../../lib/prisma.js";

/**
 * Collision Endpoints API Tests
 *
 * Tests cover:
 * - Authentication (JWT validation)
 * - Authorization (user can only see own collisions)
 * - Query parameter validation
 * - Pagination
 * - Data exposure and security
 */
describe("Collision API Endpoints", () => {
  let app: Application;
  let user1Token: string;
  let user2Token: string;
  let user3Token: string;
  let user1Id: string;
  let user2Id: string;
  let user3Id: string;

  beforeAll(async () => {
    app = createApp();

    // Create test users
    const user1 = await prisma.user.create({
      data: {
        email: "collision-user1@test.com",
        passwordHash: "hash1",
        firstName: "User",
        lastName: "One",
      },
    });

    const user2 = await prisma.user.create({
      data: {
        email: "collision-user2@test.com",
        passwordHash: "hash2",
        firstName: "User",
        lastName: "Two",
      },
    });

    const user3 = await prisma.user.create({
      data: {
        email: "collision-user3@test.com",
        passwordHash: "hash3",
        firstName: "User",
        lastName: "Three",
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
  });

  beforeEach(async () => {
    // Clean up collisions and circles before each test
    await prisma.collisionEvent.deleteMany({
      where: {
        OR: [
          { user1Id: { in: [user1Id, user2Id, user3Id] } },
          { user2Id: { in: [user1Id, user2Id, user3Id] } },
        ],
      },
    });

    await prisma.circle.deleteMany({
      where: {
        userId: { in: [user1Id, user2Id, user3Id] },
      },
    });
  });

  afterAll(async () => {
    // Cleanup test data
    await prisma.collisionEvent.deleteMany({
      where: {
        OR: [
          { user1Id: { in: [user1Id, user2Id, user3Id] } },
          { user2Id: { in: [user1Id, user2Id, user3Id] } },
        ],
      },
    });

    await prisma.circle.deleteMany({
      where: {
        userId: { in: [user1Id, user2Id, user3Id] },
      },
    });

    await prisma.user.deleteMany({
      where: {
        id: { in: [user1Id, user2Id, user3Id] },
      },
    });

    await prisma.$disconnect();
  });

  describe("GET /api/collisions - Authentication", () => {
    it("should return 401 when no authorization header", async () => {
      const response = await request(app).get("/api/collisions").expect(401);

      expect(response.body).toHaveProperty("error");
    });

    it("should return 401 when authorization header is malformed", async () => {
      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", "InvalidFormat")
        .expect(401);

      expect(response.body).toHaveProperty("error");
    });

    it("should return 401 when token is invalid", async () => {
      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", "Bearer invalid-token-here")
        .expect(401);

      expect(response.body).toHaveProperty("error");
    });

    it("should return 401 when token is expired", async () => {
      const expiredToken = jwt.sign(
        { userId: user1Id, email: "collision-user1@test.com" },
        env.jwtSecret,
        { expiresIn: "-1h" }, // Expired 1 hour ago
      );

      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${expiredToken}`)
        .expect(401);

      expect(response.body).toHaveProperty("error");
    });

    it("should return 200 when valid token provided", async () => {
      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body).toHaveProperty("collisions");
      expect(response.body).toHaveProperty("pagination");
    });
  });

  describe("GET /api/collisions - Query Parameters", () => {
    beforeEach(async () => {
      // Create circles for testing
      const circle1 = await prisma.circle.create({
        data: {
          userId: user1Id,
          objective: "Test Circle 1",
          radiusMeters: 500,
          status: "active",
          startAt: new Date(),
          expiresAt: new Date(Date.now() + 3600000),
        },
      });

      const circle2 = await prisma.circle.create({
        data: {
          userId: user2Id,
          objective: "Test Circle 2",
          radiusMeters: 500,
          status: "active",
          startAt: new Date(),
          expiresAt: new Date(Date.now() + 3600000),
        },
      });

      // Create test collisions with different statuses
      await prisma.collisionEvent.create({
        data: {
          circle1Id: circle1.id,
          circle2Id: circle2.id,
          user1Id: user1Id,
          user2Id: user2Id,
          distanceMeters: 100,
          firstSeenAt: new Date(Date.now() - 60000), // 1 min ago
          status: "detecting",
        },
      });

      await prisma.collisionEvent.create({
        data: {
          circle1Id: circle1.id,
          circle2Id: circle2.id,
          user1Id: user1Id,
          user2Id: user2Id,
          distanceMeters: 150,
          firstSeenAt: new Date(Date.now() - 120000), // 2 min ago
          status: "stable",
        },
      });
    });

    it("should apply default pagination (limit=20, offset=0)", async () => {
      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.pagination.limit).toBe(20);
      expect(response.body.pagination.offset).toBe(0);
    });

    it("should respect custom limit parameter", async () => {
      const response = await request(app)
        .get("/api/collisions?limit=5")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.pagination.limit).toBe(5);
      expect(response.body.collisions.length).toBeLessThanOrEqual(5);
    });

    it("should enforce maximum limit of 100", async () => {
      const response = await request(app)
        .get("/api/collisions?limit=10000")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.pagination.limit).toBe(100);
    });

    it("should respect offset parameter", async () => {
      const response = await request(app)
        .get("/api/collisions?offset=1")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.pagination.offset).toBe(1);
    });

    it("should filter by status (detecting)", async () => {
      const response = await request(app)
        .get("/api/collisions?status=detecting")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.collisions).toHaveLength(1);
      expect(response.body.collisions[0].status).toBe("detecting");
    });

    it("should filter by status (stable)", async () => {
      const response = await request(app)
        .get("/api/collisions?status=stable")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.collisions).toHaveLength(1);
      expect(response.body.collisions[0].status).toBe("stable");
    });

    it("should return validation error for invalid status", async () => {
      const response = await request(app)
        .get("/api/collisions?status=invalid_status")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);

      expect(response.body).toHaveProperty("error");
    });

    it("should calculate hasMore correctly", async () => {
      const response = await request(app)
        .get("/api/collisions?limit=1")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.pagination.total).toBe(2);
      expect(response.body.pagination.hasMore).toBe(true);
    });
  });

  describe("GET /api/collisions - Authorization", () => {
    let collision1Id: string;
    let collision2Id: string;

    beforeEach(async () => {
      const circle1 = await prisma.circle.create({
        data: {
          userId: user1Id,
          objective: "Circle 1",
          radiusMeters: 500,
          status: "active",
          startAt: new Date(),
          expiresAt: new Date(Date.now() + 3600000),
        },
      });

      const circle2 = await prisma.circle.create({
        data: {
          userId: user2Id,
          objective: "Circle 2",
          radiusMeters: 500,
          status: "active",
          startAt: new Date(),
          expiresAt: new Date(Date.now() + 3600000),
        },
      });

      // Collision between user1 and user2
      const collision1 = await prisma.collisionEvent.create({
        data: {
          circle1Id: circle1.id,
          circle2Id: circle2.id,
          user1Id: user1Id,
          user2Id: user2Id,
          distanceMeters: 100,
          firstSeenAt: new Date(),
          status: "detecting",
        },
      });
      collision1Id = collision1.id;

      const circle3 = await prisma.circle.create({
        data: {
          userId: user2Id,
          objective: "Circle 3",
          radiusMeters: 500,
          status: "active",
          startAt: new Date(),
          expiresAt: new Date(Date.now() + 3600000),
        },
      });

      const circle4 = await prisma.circle.create({
        data: {
          userId: user3Id,
          objective: "Circle 4",
          radiusMeters: 500,
          status: "active",
          startAt: new Date(),
          expiresAt: new Date(Date.now() + 3600000),
        },
      });

      // Collision between user2 and user3 (user1 should NOT see this)
      const collision2 = await prisma.collisionEvent.create({
        data: {
          circle1Id: circle3.id,
          circle2Id: circle4.id,
          user1Id: user2Id,
          user2Id: user3Id,
          distanceMeters: 200,
          firstSeenAt: new Date(),
          status: "stable",
        },
      });
      collision2Id = collision2.id;
    });

    it("should only return collisions where user is a participant", async () => {
      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.collisions).toHaveLength(1);
      expect(response.body.collisions[0].id).toBe(collision1Id);
    });

    it("should return different collisions for different users", async () => {
      const user3Response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user3Token}`)
        .expect(200);

      expect(user3Response.body.collisions).toHaveLength(1);
      expect(user3Response.body.collisions[0].id).toBe(collision2Id);
    });

    it("should include collisions where user is user1", async () => {
      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      const collision = response.body.collisions.find(
        (c: { id: string }) => c.id === collision1Id,
      );
      expect(collision).toBeDefined();
      expect(collision.user1Id).toBe(user1Id);
    });

    it("should include collisions where user is user2", async () => {
      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user2Token}`)
        .expect(200);

      expect(response.body.collisions).toHaveLength(2); // User2 is in both collisions
      expect(response.body.pagination.total).toBe(2);
    });
  });

  describe("GET /api/collisions/:id - Single Collision", () => {
    let collisionId: string;

    beforeEach(async () => {
      const circle1 = await prisma.circle.create({
        data: {
          userId: user1Id,
          objective: "Test Circle",
          radiusMeters: 500,
          status: "active",
          startAt: new Date(),
          expiresAt: new Date(Date.now() + 3600000),
        },
      });

      const circle2 = await prisma.circle.create({
        data: {
          userId: user2Id,
          objective: "Test Circle 2",
          radiusMeters: 500,
          status: "active",
          startAt: new Date(),
          expiresAt: new Date(Date.now() + 3600000),
        },
      });

      const collision = await prisma.collisionEvent.create({
        data: {
          circle1Id: circle1.id,
          circle2Id: circle2.id,
          user1Id: user1Id,
          user2Id: user2Id,
          distanceMeters: 150,
          firstSeenAt: new Date(),
          status: "stable",
        },
      });

      collisionId = collision.id;
    });

    it("should return 404 for non-existent collision", async () => {
      const fakeId = "00000000-0000-0000-0000-000000000000";
      const response = await request(app)
        .get(`/api/collisions/${fakeId}`)
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(404);

      expect(response.body.error).toBe("Collision not found");
    });

    it("should return 403 when user is not a participant", async () => {
      const response = await request(app)
        .get(`/api/collisions/${collisionId}`)
        .set("Authorization", `Bearer ${user3Token}`)
        .expect(403);

      expect(response.body.error).toBe("Not authorized to view this collision");
    });

    it("should return collision when user is user1", async () => {
      const response = await request(app)
        .get(`/api/collisions/${collisionId}`)
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.collision.id).toBe(collisionId);
      expect(response.body.collision.user1Id).toBe(user1Id);
      expect(response.body.collision.user2Id).toBe(user2Id);
    });

    it("should return collision when user is user2", async () => {
      const response = await request(app)
        .get(`/api/collisions/${collisionId}`)
        .set("Authorization", `Bearer ${user2Token}`)
        .expect(200);

      expect(response.body.collision.id).toBe(collisionId);
    });
  });

  describe("GET /api/collisions - Data Exposure", () => {
    beforeEach(async () => {
      const circle1 = await prisma.circle.create({
        data: {
          userId: user1Id,
          objective: "My Circle",
          radiusMeters: 500,
          status: "active",
          startAt: new Date(),
          expiresAt: new Date(Date.now() + 3600000),
        },
      });

      const circle2 = await prisma.circle.create({
        data: {
          userId: user2Id,
          objective: "Other Circle",
          radiusMeters: 300,
          status: "active",
          startAt: new Date(),
          expiresAt: new Date(Date.now() + 3600000),
        },
      });

      await prisma.collisionEvent.create({
        data: {
          circle1Id: circle1.id,
          circle2Id: circle2.id,
          user1Id: user1Id,
          user2Id: user2Id,
          distanceMeters: 175,
          firstSeenAt: new Date(),
          status: "stable",
        },
      });
    });

    it("should include circle data in response", async () => {
      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      const collision = response.body.collisions[0];
      expect(collision.circle1).toBeDefined();
      expect(collision.circle1.objective).toBe("My Circle");
      expect(collision.circle1.radiusMeters).toBe(500);
      expect(collision.circle2).toBeDefined();
      expect(collision.circle2.objective).toBe("Other Circle");
    });

    it("should include user data in response", async () => {
      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      const collision = response.body.collisions[0];
      expect(collision.user1).toBeDefined();
      expect(collision.user1.email).toBe("collision-user1@test.com");
      expect(collision.user1.firstName).toBe("User");
      expect(collision.user2).toBeDefined();
      expect(collision.user2.email).toBe("collision-user2@test.com");
    });

    it("should NOT expose password hashes", async () => {
      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      const collision = response.body.collisions[0];
      expect(collision.user1.passwordHash).toBeUndefined();
      expect(collision.user2.passwordHash).toBeUndefined();
    });

    it("should include distance in meters", async () => {
      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      const collision = response.body.collisions[0];
      expect(collision.distanceMeters).toBe(175);
    });

    it("should include timestamps", async () => {
      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      const collision = response.body.collisions[0];
      expect(collision.firstSeenAt).toBeDefined();
      expect(collision.detectedAt).toBeDefined();
    });
  });

  describe("GET /api/collisions - Edge Cases", () => {
    it("should return empty array when user has no collisions", async () => {
      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.collisions).toEqual([]);
      expect(response.body.pagination.total).toBe(0);
      expect(response.body.pagination.hasMore).toBe(false);
    });

    it("should handle offset beyond total results", async () => {
      const response = await request(app)
        .get("/api/collisions?offset=1000")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.collisions).toEqual([]);
      expect(response.body.pagination.hasMore).toBe(false);
    });

    it("should return 400 for negative limit", async () => {
      const response = await request(app)
        .get("/api/collisions?limit=-1")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);

      expect(response.body).toHaveProperty("error");
    });

    it("should return 400 for negative offset", async () => {
      const response = await request(app)
        .get("/api/collisions?offset=-10")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);

      expect(response.body).toHaveProperty("error");
    });

    it("should return 400 for non-numeric limit", async () => {
      const response = await request(app)
        .get("/api/collisions?limit=abc")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);

      expect(response.body).toHaveProperty("error");
    });
  });
});
