import { describe, it, expect, beforeEach, vi } from "vitest";

import { COLLISION_CONFIG } from "../config/collision.config.js";
import { CollisionDetectionService } from "../services/collision-detection-service.js";

// In-memory stores for mocks
const circles: Array<{
  id: string;
  userId: string;
  status: string;
  radiusMeters: number;
  objective: string;
  expiresAt: Date;
  startAt: Date;
  createdAt: Date;
}> = [];

const users: Array<{
  id: string;
  centerLat: number | null;
  centerLon: number | null;
}> = [];

const collisionEvents: Array<{
  id: string;
  circle1Id: string;
  circle2Id: string;
  user1Id: string;
  user2Id: string;
  distanceMeters: number;
  firstSeenAt: Date;
  detectedAt: Date;
  status: string;
}> = [];

const redisHashes = new Map<string, Record<string, string>>();
const redisSortedSets = new Map<
  string,
  Array<{ score: number; value: string }>
>();
const redisExpires = new Map<string, number>();

// Mock Prisma
vi.mock("../lib/prisma.js", () => {
  const prisma = {
    circle: {
      findFirst: vi.fn(
        async ({
          where,
          orderBy,
          select,
        }: {
          where?: {
            userId?: string;
            status?: string;
            expiresAt?: { gt?: Date };
            startAt?: { lte?: Date };
          };
          orderBy?: Record<string, string>;
          select?: Record<string, boolean>;
        }) => {
          let filtered = circles.filter((c) => {
            if (where?.userId && c.userId !== where.userId) return false;
            if (where?.status && c.status !== where.status) return false;
            if (where?.expiresAt?.gt && c.expiresAt <= where.expiresAt.gt)
              return false;
            if (where?.startAt?.lte && c.startAt > where.startAt.lte)
              return false;
            return true;
          });

          if (orderBy?.createdAt === "desc") {
            filtered = filtered.sort(
              (a, b) => b.createdAt.getTime() - a.createdAt.getTime(),
            );
          }

          const result = filtered[0] || null;

          // Handle select clause - only return selected fields
          if (result && select) {
            const selectedFields: Record<string, unknown> = {};
            Object.keys(select).forEach((key) => {
              if (select[key] && key in result) {
                selectedFields[key] = result[key as keyof typeof result];
              }
            });
            return selectedFields;
          }

          return result;
        },
      ),
    },
    collisionEvent: {
      create: vi.fn(
        async ({
          data,
        }: {
          data: {
            circle1Id: string;
            circle2Id: string;
            user1Id: string;
            user2Id: string;
            distanceMeters: number;
            firstSeenAt: Date;
            status: string;
          };
        }) => {
          const event = {
            id: `collision-event-${collisionEvents.length + 1}`,
            ...data,
            detectedAt: data.firstSeenAt,
          };
          collisionEvents.push(event);
          return event;
        },
      ),
      update: vi.fn(
        async ({
          where,
          data,
        }: {
          where: {
            unique_collision_pair?: { circle1Id: string; circle2Id: string };
          };
          data: Record<string, unknown>;
        }) => {
          const { circle1Id, circle2Id } = where.unique_collision_pair || {};
          const event = collisionEvents.find(
            (e) => e.circle1Id === circle1Id && e.circle2Id === circle2Id,
          );
          if (!event) {
            throw new Error("CollisionEvent not found");
          }
          Object.assign(event, data);
          return event;
        },
      ),
    },
    $queryRaw: vi.fn(async (_query: unknown, ...params: unknown[]) => {
      // Mock PostGIS query - returns circles near the user's position
      // Extract userId from query params (it's in the WHERE clause)
      const userId = params.find(
        (p) => typeof p === "string" && p.startsWith("user-"),
      );

      const now = new Date();
      return circles
        .filter((c) => {
          // Exclude circles owned by the querying user
          if (c.userId === userId) return false;
          return c.status === "active" && c.expiresAt > now && c.startAt <= now;
        })
        .map((c) => {
          const user = users.find((u) => u.id === c.userId);
          if (!user || user.centerLat === null || user.centerLon === null) {
            return null;
          }

          // Simple distance calculation (mock - not real haversine)
          const distance = Math.random() * c.radiusMeters * 0.8; // Within radius

          return {
            id: c.id,
            userId: c.userId,
            radiusMeters: c.radiusMeters,
            objective: c.objective,
            distance_meters: distance,
          };
        })
        .filter(Boolean)
        .slice(0, COLLISION_CONFIG.SPATIAL_INDEX_SEARCH_LIMIT);
    }),
  };

  return { prisma };
});

// Mock Redis
vi.mock("../infrastructure/redis.js", () => ({
  getRedisClient: vi.fn(() => ({
    hgetall: vi.fn(async (key: string) => {
      return redisHashes.get(key) || {};
    }),
    hset: vi.fn(
      async (
        key: string,
        data: Record<string, unknown> | string,
        value?: unknown,
      ) => {
        const existing = redisHashes.get(key) || {};
        if (typeof data === "string") {
          // Handle hset(key, field, value) format
          redisHashes.set(key, { ...existing, [data]: String(value) });
        } else {
          // Handle hset(key, { field1: value1, field2: value2 }) format
          const stringified: Record<string, string> = {};
          for (const [k, v] of Object.entries(data)) {
            stringified[k] = String(v);
          }
          redisHashes.set(key, { ...existing, ...stringified });
        }
        return 1;
      },
    ),
    zadd: vi.fn(async (key: string, score: number, value: string) => {
      const set = redisSortedSets.get(key) || [];
      set.push({ score, value });
      redisSortedSets.set(key, set);
      return 1;
    }),
    expire: vi.fn(async (key: string, seconds: number) => {
      redisExpires.set(key, Date.now() + seconds * 1000);
      return 1;
    }),
    zrangebyscore: vi.fn(
      async (key: string, min: string | number, max: string | number) => {
        const set = redisSortedSets.get(key) || [];
        const minScore = min === "-inf" ? -Infinity : Number(min);
        const maxScore = max === "+inf" ? Infinity : Number(max);
        return set
          .filter((item) => item.score >= minScore && item.score <= maxScore)
          .map((item) => item.value);
      },
    ),
    zrem: vi.fn(async (key: string, value: string) => {
      const set = redisSortedSets.get(key) || [];
      const filtered = set.filter((item) => item.value !== value);
      redisSortedSets.set(key, filtered);
      return 1;
    }),
    del: vi.fn(async (key: string) => {
      redisHashes.delete(key);
      return 1;
    }),
  })),
}));

describe("CollisionDetectionService", () => {
  let service: CollisionDetectionService;

  beforeEach(() => {
    // Clear all stores
    circles.length = 0;
    users.length = 0;
    collisionEvents.length = 0;
    redisHashes.clear();
    redisSortedSets.clear();
    redisExpires.clear();

    // Clear all mock call histories
    vi.clearAllMocks();

    service = new CollisionDetectionService();
  });

  describe("detectCollisionsForUser", () => {
    it("detects collision when user position is within another user's circle", async () => {
      // Setup: User 2 has an active circle at position (10, 10) with 500m radius
      users.push(
        { id: "user-1", centerLat: 10.0, centerLon: 10.0 },
        { id: "user-2", centerLat: 10.001, centerLon: 10.001 },
      );

      // User 1 has an active circle (created first - older)
      circles.push({
        id: "circle-1",
        userId: "user-1",
        status: "active",
        radiusMeters: 500,
        objective: "Coffee meetup",
        expiresAt: new Date(Date.now() + 3600000),
        startAt: new Date(Date.now() - 3600000),
        createdAt: new Date(Date.now() - 10000), // Older
      });

      // User 2 has an active circle
      circles.push({
        id: "circle-2",
        userId: "user-2",
        status: "active",
        radiusMeters: 500,
        objective: "Developer networking",
        expiresAt: new Date(Date.now() + 3600000),
        startAt: new Date(Date.now() - 3600000),
        createdAt: new Date(),
      });

      // Act: User 1 moves to position near User 2's circle
      const collisions = await service.detectCollisionsForUser(
        "user-1",
        10.001,
        10.001,
      );

      // Assert
      expect(collisions.length).toBeGreaterThan(0);
      expect(collisions[0].user1Id).toBe("user-1");
      expect(collisions[0].circle1Id).toBe("circle-1"); // Uses user-1's circle
    });

    it("skips collision if visitor has no active circles", async () => {
      // Setup: User 2 has circle, but User 1 has NO circles
      users.push(
        { id: "user-1", centerLat: 10.0, centerLon: 10.0 },
        { id: "user-2", centerLat: 10.001, centerLon: 10.001 },
      );

      circles.push({
        id: "circle-2",
        userId: "user-2",
        status: "active",
        radiusMeters: 500,
        objective: "Developer networking",
        expiresAt: new Date(Date.now() + 3600000),
        startAt: new Date(Date.now() - 3600000),
        createdAt: new Date(),
      });

      // Act: User 1 (no circles) moves near User 2's circle
      const collisions = await service.detectCollisionsForUser(
        "user-1",
        10.001,
        10.001,
      );

      // Assert: No collisions tracked because visitor has no circle
      expect(collisions).toEqual([]);
      expect(collisionEvents).toHaveLength(0);
    });

    it("limits collisions to MAX_COLLISIONS_PER_UPDATE", async () => {
      // Setup: Create 20 circles, but should only return top 10
      users.push({ id: "user-visitor", centerLat: 10.0, centerLon: 10.0 });

      // Visitor needs a circle
      circles.push({
        id: "circle-visitor",
        userId: "user-visitor",
        status: "active",
        radiusMeters: 300,
        objective: "Visitor circle",
        expiresAt: new Date(Date.now() + 3600000),
        startAt: new Date(Date.now() - 3600000),
        createdAt: new Date(),
      });

      for (let i = 0; i < 20; i++) {
        users.push({ id: `user-${i}`, centerLat: 10.001, centerLon: 10.001 });
        circles.push({
          id: `circle-${i}`,
          userId: `user-${i}`,
          status: "active",
          radiusMeters: 1000,
          objective: `Circle ${i}`,
          expiresAt: new Date(Date.now() + 3600000),
          startAt: new Date(Date.now() - 3600000),
          createdAt: new Date(),
        });
      }

      // Act
      const collisions = await service.detectCollisionsForUser(
        "user-visitor",
        10.001,
        10.001,
      );

      // Assert: Should be limited to MAX_COLLISIONS_PER_UPDATE (10)
      expect(collisions.length).toBeLessThanOrEqual(
        COLLISION_CONFIG.MAX_COLLISIONS_PER_UPDATE,
      );
    });

    it("handles errors gracefully and returns empty array", async () => {
      // Setup: Add a circle for user-1 so collision detection will proceed
      circles.push({
        id: "circle-1",
        userId: "user-1",
        status: "active",
        radiusMeters: 300,
        objective: "Test",
        expiresAt: new Date(Date.now() + 3600000),
        startAt: new Date(Date.now() - 3600000),
        createdAt: new Date(),
      });

      // Force an error by making $queryRaw throw
      const { prisma } = await import("../lib/prisma.js");
      vi.mocked(prisma.$queryRaw).mockRejectedValueOnce(
        new Error("Database error"),
      );

      // Act
      const collisions = await service.detectCollisionsForUser(
        "user-1",
        10.0,
        10.0,
      );

      // Assert: Should return empty array on error
      expect(collisions).toEqual([]);
    });
  });

  describe("trackCollisionStability", () => {
    it("creates CollisionEvent on first detection", async () => {
      // Arrange
      const collision = {
        circle1Id: "circle-1",
        circle2Id: "circle-2",
        user1Id: "user-1",
        user2Id: "user-2",
        distance: 150,
        timestamp: Date.now(),
      };

      // Act
      await service.trackCollisionStability(collision);

      // Assert: CollisionEvent created
      expect(collisionEvents).toHaveLength(1);
      expect(collisionEvents[0]).toMatchObject({
        circle1Id: "circle-1",
        circle2Id: "circle-2",
        user1Id: "user-1",
        user2Id: "user-2",
        distanceMeters: 150,
        status: "detecting",
      });
    });

    it("adds collision to stability queue on first detection", async () => {
      // Arrange
      const collision = {
        circle1Id: "circle-1",
        circle2Id: "circle-2",
        user1Id: "user-1",
        user2Id: "user-2",
        distance: 150,
        timestamp: Date.now(),
      };

      // Act
      await service.trackCollisionStability(collision);

      // Assert: Added to stability queue
      const queue = redisSortedSets.get(
        COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue,
      );
      expect(queue).toBeDefined();
      expect(queue!.length).toBe(1);
    });

    it("updates collision on subsequent detections", async () => {
      // Arrange: First detection
      const collision = {
        circle1Id: "circle-1",
        circle2Id: "circle-2",
        user1Id: "user-1",
        user2Id: "user-2",
        distance: 150,
        timestamp: Date.now(),
      };

      await service.trackCollisionStability(collision);

      // Act: Second detection with different distance
      const updatedCollision = {
        ...collision,
        distance: 120,
        timestamp: Date.now(),
      };
      await service.trackCollisionStability(updatedCollision);

      // Assert: Should update, not create new
      expect(collisionEvents).toHaveLength(1);
      expect(collisionEvents[0].distanceMeters).toBe(120);
    });

    it("promotes collision to stable after stability window", async () => {
      // Arrange: Create collision with old timestamp
      const oldTimestamp =
        Date.now() - COLLISION_CONFIG.STABILITY_WINDOW_MS - 1000;
      const collision = {
        circle1Id: "circle-1",
        circle2Id: "circle-2",
        user1Id: "user-1",
        user2Id: "user-2",
        distance: 150,
        timestamp: oldTimestamp,
      };

      // Manually set up Redis state to simulate first detection
      const redisKey = COLLISION_CONFIG.REDIS_KEYS.collisionActive(
        "circle-1",
        "circle-2",
      );
      redisHashes.set(redisKey, {
        firstSeenAt: String(oldTimestamp),
        detectedAt: String(oldTimestamp),
        status: "detecting",
        distance: "150",
        user1Id: "user-1",
        user2Id: "user-2",
        circle1Id: "circle-1",
        circle2Id: "circle-2",
      });

      // Create collision event
      collisionEvents.push({
        id: "collision-1",
        circle1Id: "circle-1",
        circle2Id: "circle-2",
        user1Id: "user-1",
        user2Id: "user-2",
        distanceMeters: 150,
        firstSeenAt: new Date(oldTimestamp),
        detectedAt: new Date(oldTimestamp),
        status: "detecting",
      });

      // Act: Detect again after stability window
      const newCollision = { ...collision, timestamp: Date.now() };
      await service.trackCollisionStability(newCollision);

      // Assert: Status should be updated to stable
      const redisState = redisHashes.get(redisKey);
      expect(redisState?.status).toBe("stable");
      expect(collisionEvents[0].status).toBe("stable");
    });

    it("returns early if circle1Id is null", async () => {
      // Arrange
      const collision = {
        circle1Id: null,
        circle2Id: "circle-2",
        user1Id: "user-1",
        user2Id: "user-2",
        distance: 150,
        timestamp: Date.now(),
      };

      // Act
      await service.trackCollisionStability(collision);

      // Assert: Should not create any events
      expect(collisionEvents).toHaveLength(0);
      expect(redisHashes.size).toBe(0);
    });

    it("sets TTL on Redis collision key", async () => {
      // Arrange
      const collision = {
        circle1Id: "circle-1",
        circle2Id: "circle-2",
        user1Id: "user-1",
        user2Id: "user-2",
        distance: 150,
        timestamp: Date.now(),
      };

      // Act
      await service.trackCollisionStability(collision);

      // Assert: TTL should be set
      const redisKey = COLLISION_CONFIG.REDIS_KEYS.collisionActive(
        "circle-1",
        "circle-2",
      );
      expect(redisExpires.has(redisKey)).toBe(true);
    });
  });

  describe("processStabilityQueue", () => {
    it("processes empty queue without errors", async () => {
      // Act & Assert: Should not throw
      await expect(service.processStabilityQueue()).resolves.toBeUndefined();
    });

    it("removes stale collisions from queue", async () => {
      // Arrange: Add stale collision to queue
      const queueKey = COLLISION_CONFIG.REDIS_KEYS.collisionStabilityQueue;
      const collisionKey = "circle-1:circle-2";

      redisSortedSets.set(queueKey, [
        {
          score: Date.now() - COLLISION_CONFIG.STABILITY_WINDOW_MS - 1000,
          value: collisionKey,
        },
      ]);

      // Act
      await service.processStabilityQueue();

      // Assert: Queue should process the collision (removed if no active Redis state)
      const queue = redisSortedSets.get(queueKey);
      expect(queue).toBeDefined();
      // The collision should be removed since there's no active Redis state
      expect(queue!.length).toBe(0);
    });
  });

  describe("integration: full collision flow", () => {
    it("handles complete flow from detection to stable promotion", async () => {
      // Setup
      users.push(
        { id: "user-1", centerLat: 10.0, centerLon: 10.0 },
        { id: "user-2", centerLat: 10.001, centerLon: 10.001 },
      );

      circles.push(
        {
          id: "circle-1",
          userId: "user-1",
          status: "active",
          radiusMeters: 300,
          objective: "Coffee",
          expiresAt: new Date(Date.now() + 3600000),
          startAt: new Date(Date.now() - 3600000),
          createdAt: new Date(),
        },
        {
          id: "circle-2",
          userId: "user-2",
          status: "active",
          radiusMeters: 500,
          objective: "Networking",
          expiresAt: new Date(Date.now() + 3600000),
          startAt: new Date(Date.now() - 3600000),
          createdAt: new Date(),
        },
      );

      // Step 1: First detection
      const collisions1 = await service.detectCollisionsForUser(
        "user-1",
        10.001,
        10.001,
      );
      expect(collisions1.length).toBeGreaterThan(0);

      // Should detect collision with user-2's circle only (not user-1's own circle)
      const user2Collision = collisions1.find((c) => c.user2Id === "user-2");
      expect(user2Collision).toBeDefined();
      expect(user2Collision!.circle1Id).toBe("circle-1"); // visitor's circle
      expect(user2Collision!.circle2Id).toBe("circle-2"); // target circle

      // Step 2: Simulate time passing and detect again
      const oldTimestamp =
        Date.now() - COLLISION_CONFIG.STABILITY_WINDOW_MS - 1000;
      const redisKey = COLLISION_CONFIG.REDIS_KEYS.collisionActive(
        "circle-1",
        "circle-2",
      );
      redisHashes.set(redisKey, {
        firstSeenAt: String(oldTimestamp),
        detectedAt: String(oldTimestamp),
        status: "detecting",
        distance: "150",
        user1Id: "user-1",
        user2Id: "user-2",
        circle1Id: "circle-1",
        circle2Id: "circle-2",
      });

      // Update the collision event to have the old timestamp
      const collisionEvent = collisionEvents.find(
        (e) => e.circle1Id === "circle-1" && e.circle2Id === "circle-2",
      );
      if (collisionEvent) {
        collisionEvent.firstSeenAt = new Date(oldTimestamp);
      }

      // Detect again
      await service.trackCollisionStability({
        ...user2Collision!,
        timestamp: Date.now(),
      });

      // Step 3: Verify promotion to stable
      const finalState = redisHashes.get(redisKey);
      expect(finalState?.status).toBe("stable");

      // Find the correct collision event
      const stableEvent = collisionEvents.find(
        (e) => e.circle1Id === "circle-1" && e.circle2Id === "circle-2",
      );
      expect(stableEvent?.status).toBe("stable");
    });
  });
});
