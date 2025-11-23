import type { Application } from "express";
import jwt from "jsonwebtoken";
import request from "supertest";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

import { createApp } from "../../app.js";
import { env } from "../../config/env.js";

// Mock Prisma
vi.mock("../../lib/prisma.js", () => ({
  prisma: {
    collisionEvent: {
      findMany: vi.fn(),
      findUnique: vi.fn(),
      count: vi.fn(),
    },
  },
}));

import { prisma } from "../../lib/prisma.js";

describe("Collision API Endpoints", () => {
  let app: Application;
  let user1Token: string;
  let user2Token: string;
  let user3Token: string;
  const user1Id = "test-user-1";
  const user2Id = "test-user-2";
  const user3Id = "test-user-3";

  const mockCollision = {
    id: "collision-1",
    circle1Id: "circle-1",
    circle2Id: "circle-2",
    user1Id: user1Id,
    user2Id: user2Id,
    distanceMeters: 100,
    firstSeenAt: new Date(),
    detectedAt: new Date(),
    status: "detecting",
    user1: {
      id: user1Id,
      email: "user1@test.com",
      firstName: "User",
      lastName: "One",
    },
    user2: {
      id: user2Id,
      email: "user2@test.com",
      firstName: "User",
      lastName: "Two",
    },
    circle1: {
      id: "circle-1",
      objective: "Test Objective 1",
      radiusMeters: 500,
      userId: user1Id,
    },
    circle2: {
      id: "circle-2",
      objective: "Test Objective 2",
      radiusMeters: 500,
      userId: user2Id,
    },
    mission: null,
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
    vi.mocked(prisma.collisionEvent.findMany).mockResolvedValue([]);
    vi.mocked(prisma.collisionEvent.count).mockResolvedValue(0);
    vi.mocked(prisma.collisionEvent.findUnique).mockResolvedValue(null);
  });

  describe("GET /api/collisions - Authentication", () => {
    it("should return 401 when no authorization header", async () => {
      await request(app).get("/api/collisions").expect(401);
    });

    it("should return 401 when authorization header is malformed", async () => {
      await request(app)
        .get("/api/collisions")
        .set("Authorization", "InvalidFormat")
        .expect(401);
    });

    it("should return 401 when token is invalid", async () => {
      await request(app)
        .get("/api/collisions")
        .set("Authorization", "Bearer invalid-token")
        .expect(401);
    });

    it("should return 401 when token is expired", async () => {
      const expiredToken = jwt.sign(
        { userId: user1Id, email: "user1@test.com" },
        env.jwtSecret,
        { expiresIn: "-1h" },
      );

      await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${expiredToken}`)
        .expect(401);
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
    });

    it("should enforce maximum limit of 100", async () => {
      const response = await request(app)
        .get("/api/collisions?limit=10000")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);

      expect(response.body).toHaveProperty("error");
    });

    it("should respect offset parameter", async () => {
      const response = await request(app)
        .get("/api/collisions?offset=10")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.pagination.offset).toBe(10);
    });

    it("should filter by status (detecting)", async () => {
      vi.mocked(prisma.collisionEvent.findMany).mockResolvedValue([
        mockCollision,
      ]);
      vi.mocked(prisma.collisionEvent.count).mockResolvedValue(1);

      const response = await request(app)
        .get("/api/collisions?status=detecting")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.collisions).toHaveLength(1);
    });

    it("should return validation error for invalid status", async () => {
      const response = await request(app)
        .get("/api/collisions?status=invalid")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);

      expect(response.body).toHaveProperty("error");
    });

    it("should return 400 for negative limit", async () => {
      await request(app)
        .get("/api/collisions?limit=-1")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);
    });

    it("should return 400 for negative offset", async () => {
      await request(app)
        .get("/api/collisions?offset=-10")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);
    });

    it("should return 400 for non-numeric limit", async () => {
      await request(app)
        .get("/api/collisions?limit=abc")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(400);
    });

    it("should calculate hasMore correctly", async () => {
      vi.mocked(prisma.collisionEvent.count).mockResolvedValue(25);

      const response = await request(app)
        .get("/api/collisions?limit=20&offset=0")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.pagination.hasMore).toBe(true);
    });
  });

  describe("GET /api/collisions - Authorization", () => {
    it("should only return collisions where user is a participant", async () => {
      vi.mocked(prisma.collisionEvent.findMany).mockResolvedValue([
        mockCollision,
      ]);
      vi.mocked(prisma.collisionEvent.count).mockResolvedValue(1);

      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      // Verify WHERE clause was built correctly
      expect(prisma.collisionEvent.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            OR: [{ user1Id: user1Id }, { user2Id: user1Id }],
          }),
        }),
      );

      expect(response.body.collisions).toHaveLength(1);
    });

    it("should return different collisions for different users", async () => {
      vi.mocked(prisma.collisionEvent.findMany).mockResolvedValue([]);

      await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user3Token}`)
        .expect(200);

      expect(prisma.collisionEvent.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            OR: [{ user1Id: user3Id }, { user2Id: user3Id }],
          }),
        }),
      );
    });
  });

  describe("GET /api/collisions/:id - Single Collision", () => {
    it("should return 404 for non-existent collision", async () => {
      vi.mocked(prisma.collisionEvent.findUnique).mockResolvedValue(null);

      await request(app)
        .get("/api/collisions/non-existent-id")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(404);
    });

    it("should return 403 when user is not a participant", async () => {
      vi.mocked(prisma.collisionEvent.findUnique).mockResolvedValue({
        ...mockCollision,
        user1Id: "other-user",
        user2Id: "another-user",
      });

      await request(app)
        .get("/api/collisions/collision-1")
        .set("Authorization", `Bearer ${user3Token}`)
        .expect(403);
    });

    it("should return collision when user is user1", async () => {
      vi.mocked(prisma.collisionEvent.findUnique).mockResolvedValue(
        mockCollision,
      );

      const response = await request(app)
        .get("/api/collisions/collision-1")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.collision.id).toBe("collision-1");
    });

    it("should return collision when user is user2", async () => {
      vi.mocked(prisma.collisionEvent.findUnique).mockResolvedValue(
        mockCollision,
      );

      const response = await request(app)
        .get("/api/collisions/collision-1")
        .set("Authorization", `Bearer ${user2Token}`)
        .expect(200);

      expect(response.body.collision.id).toBe("collision-1");
    });
  });

  describe("GET /api/collisions - Data Exposure", () => {
    it("should include circle data in response", async () => {
      vi.mocked(prisma.collisionEvent.findMany).mockResolvedValue([
        mockCollision,
      ]);
      vi.mocked(prisma.collisionEvent.count).mockResolvedValue(1);

      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      const collision = response.body.collisions[0];
      expect(collision.circle1).toHaveProperty("id");
      expect(collision.circle1).toHaveProperty("objective");
      expect(collision.circle1).toHaveProperty("radiusMeters");
    });

    it("should include user data in response", async () => {
      vi.mocked(prisma.collisionEvent.findMany).mockResolvedValue([
        mockCollision,
      ]);
      vi.mocked(prisma.collisionEvent.count).mockResolvedValue(1);

      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      const collision = response.body.collisions[0];
      expect(collision.user1).toHaveProperty("id");
      expect(collision.user1).toHaveProperty("email");
      expect(collision.user1).toHaveProperty("firstName");
      expect(collision.user1).toHaveProperty("lastName");
    });

    it("should NOT expose password hashes", async () => {
      vi.mocked(prisma.collisionEvent.findMany).mockResolvedValue([
        mockCollision,
      ]);
      vi.mocked(prisma.collisionEvent.count).mockResolvedValue(1);

      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      const collision = response.body.collisions[0];
      expect(collision.user1.passwordHash).toBeUndefined();
      expect(collision.user2.passwordHash).toBeUndefined();
    });

    it("should include distance in meters", async () => {
      vi.mocked(prisma.collisionEvent.findMany).mockResolvedValue([
        mockCollision,
      ]);
      vi.mocked(prisma.collisionEvent.count).mockResolvedValue(1);

      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.collisions[0]).toHaveProperty("distanceMeters");
    });

    it("should include timestamps", async () => {
      vi.mocked(prisma.collisionEvent.findMany).mockResolvedValue([
        mockCollision,
      ]);
      vi.mocked(prisma.collisionEvent.count).mockResolvedValue(1);

      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      const collision = response.body.collisions[0];
      expect(collision).toHaveProperty("firstSeenAt");
      expect(collision).toHaveProperty("detectedAt");
    });
  });

  describe("GET /api/collisions - Edge Cases", () => {
    it("should return empty array when user has no collisions", async () => {
      vi.mocked(prisma.collisionEvent.findMany).mockResolvedValue([]);
      vi.mocked(prisma.collisionEvent.count).mockResolvedValue(0);

      const response = await request(app)
        .get("/api/collisions")
        .set("Authorization", `Bearer ${user3Token}`)
        .expect(200);

      expect(response.body.collisions).toEqual([]);
      expect(response.body.pagination.total).toBe(0);
    });

    it("should handle offset beyond total results", async () => {
      vi.mocked(prisma.collisionEvent.findMany).mockResolvedValue([]);
      vi.mocked(prisma.collisionEvent.count).mockResolvedValue(5);

      const response = await request(app)
        .get("/api/collisions?offset=100")
        .set("Authorization", `Bearer ${user1Token}`)
        .expect(200);

      expect(response.body.collisions).toEqual([]);
    });
  });
});
