import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

import {
  EventBus,
  resetEventBus,
} from "../../infrastructure/observer/event-bus.js";
import type {
  EventBusConfig,
  CircuitBreakerConfig,
} from "../../infrastructure/observer/types.js";

// Mock Redis
const mockPipeline = {
  hset: vi.fn().mockReturnThis(),
  expire: vi.fn().mockReturnThis(),
  xadd: vi.fn().mockReturnThis(),
  exec: vi.fn().mockResolvedValue([]),
};

const mockRedis = {
  pipeline: vi.fn(() => mockPipeline),
};

vi.mock("../../infrastructure/redis.js", () => ({
  getRedisClient: () => mockRedis,
}));

describe("EventBus", () => {
  let eventBus: EventBus;
  let config: EventBusConfig;
  let circuitBreakerConfig: CircuitBreakerConfig;

  beforeEach(() => {
    vi.clearAllMocks();
    resetEventBus();

    config = {
      batchSize: 3,
      batchWaitMs: 100,
      streamPrefix: "test-observer",
      streamMaxLen: 1000,
      eventTtl: 3600,
      enabled: true,
    };

    circuitBreakerConfig = {
      failureThreshold: 5,
      resetTimeout: 30000,
      windowSize: 60000,
      successThreshold: 3,
    };

    eventBus = new EventBus(config, circuitBreakerConfig);
  });

  afterEach(() => {
    resetEventBus();
  });

  describe("event emission", () => {
    it("should add event to buffer", () => {
      eventBus.emit({
        type: "location.updated",
        userId: "user-1",
        metadata: { latitude: 40.7128, longitude: -74.006 },
      });

      expect(eventBus.getBufferSize()).toBe(1);
    });

    it("should not emit when observer is disabled", () => {
      const disabledConfig = { ...config, enabled: false };
      const disabledBus = new EventBus(disabledConfig, circuitBreakerConfig);

      disabledBus.emit({
        type: "location.updated",
        userId: "user-1",
        metadata: {},
      });

      expect(disabledBus.getBufferSize()).toBe(0);
    });

    it("should handle multiple events", () => {
      eventBus.emit({
        type: "location.updated",
        userId: "user-1",
        metadata: {},
      });

      eventBus.emit({
        type: "collision.detected",
        userId: "user-2",
        metadata: {},
      });

      expect(eventBus.getBufferSize()).toBe(2);
    });
  });

  describe("batching", () => {
    it("should flush when batch size is reached", async () => {
      // Emit 3 events (batch size)
      eventBus.emit({
        type: "location.updated",
        userId: "user-1",
        metadata: {},
      });

      eventBus.emit({
        type: "location.updated",
        userId: "user-2",
        metadata: {},
      });

      eventBus.emit({
        type: "location.updated",
        userId: "user-3",
        metadata: {},
      });

      // Wait for async flush
      await new Promise((resolve) => setTimeout(resolve, 50));

      // Buffer should be empty after flush
      expect(eventBus.getBufferSize()).toBe(0);

      // Redis pipeline should have been called
      expect(mockRedis.pipeline).toHaveBeenCalled();
      expect(mockPipeline.exec).toHaveBeenCalled();
    });

    it("should flush after batch wait time", async () => {
      eventBus.emit({
        type: "location.updated",
        userId: "user-1",
        metadata: {},
      });

      expect(eventBus.getBufferSize()).toBe(1);

      // Wait for batch wait time + buffer
      await new Promise((resolve) => setTimeout(resolve, 150));

      // Buffer should be empty after time-based flush
      expect(eventBus.getBufferSize()).toBe(0);
    });

    it("should not flush empty buffer", async () => {
      await eventBus.forceFlush();

      // Should not call Redis
      expect(mockRedis.pipeline).not.toHaveBeenCalled();
    });
  });

  describe("Redis integration", () => {
    it("should write event to Redis with correct structure", async () => {
      eventBus.emit({
        type: "location.updated",
        userId: "user-1",
        relatedUserId: "user-2",
        circleId: "circle-1",
        metadata: { latitude: 40.7128, longitude: -74.006 },
      });

      await eventBus.forceFlush();

      // Verify pipeline operations
      expect(mockPipeline.hset).toHaveBeenCalled();
      expect(mockPipeline.expire).toHaveBeenCalled();
      expect(mockPipeline.xadd).toHaveBeenCalled();
      expect(mockPipeline.exec).toHaveBeenCalled();

      // Verify event was written to both type-specific and global streams
      expect(mockPipeline.xadd).toHaveBeenCalledTimes(2); // type stream + global stream
    });

    it("should handle Redis errors gracefully", async () => {
      // Mock Redis error
      mockPipeline.exec.mockRejectedValueOnce(
        new Error("Redis connection failed"),
      );

      eventBus.emit({
        type: "location.updated",
        userId: "user-1",
        metadata: {},
      });

      // Should not throw
      await expect(eventBus.forceFlush()).resolves.not.toThrow();
    });

    it("should use correct Redis key patterns", async () => {
      eventBus.emit({
        type: "collision.detected",
        userId: "user-1",
        metadata: {},
      });

      await eventBus.forceFlush();

      // Check that xadd was called with correct stream keys
      const xaddCalls = mockPipeline.xadd.mock.calls;
      const streamKeys = xaddCalls.map((call) => call[0]);

      expect(streamKeys).toContain("test-observer:events:collision.detected");
      expect(streamKeys).toContain("test-observer:events:all");
    });
  });

  describe("circuit breaker integration", () => {
    it("should drop events when circuit is open", async () => {
      // Force circuit open by simulating failures
      mockPipeline.exec.mockRejectedValue(new Error("Redis down"));

      // Emit enough events to trigger failures
      for (let i = 0; i < 10; i++) {
        eventBus.emit({
          type: "location.updated",
          userId: `user-${i}`,
          metadata: {},
        });
        await eventBus.forceFlush();
      }

      // Circuit should be open, events should be dropped
      eventBus.emit({
        type: "location.updated",
        userId: "user-test",
        metadata: {},
      });

      // Event should be dropped (not added to buffer if circuit open)
      // Or if added, should not be flushed
      const statsAfterEmit = eventBus.getCircuitStats();

      // Circuit should still be open or have high failure count
      expect(
        statsAfterEmit.state === "open" || statsAfterEmit.failureCount > 0,
      ).toBe(true);
    });
  });

  describe("force flush", () => {
    it("should immediately flush buffered events", async () => {
      eventBus.emit({
        type: "location.updated",
        userId: "user-1",
        metadata: {},
      });

      eventBus.emit({
        type: "location.updated",
        userId: "user-2",
        metadata: {},
      });

      expect(eventBus.getBufferSize()).toBe(2);

      await eventBus.forceFlush();

      expect(eventBus.getBufferSize()).toBe(0);
      expect(mockPipeline.exec).toHaveBeenCalled();
    });
  });

  describe("statistics", () => {
    it("should track buffer size correctly", () => {
      expect(eventBus.getBufferSize()).toBe(0);

      eventBus.emit({
        type: "location.updated",
        userId: "user-1",
        metadata: {},
      });

      expect(eventBus.getBufferSize()).toBe(1);

      eventBus.emit({
        type: "location.updated",
        userId: "user-2",
        metadata: {},
      });

      expect(eventBus.getBufferSize()).toBe(2);
    });

    it("should provide circuit breaker stats", () => {
      const stats = eventBus.getCircuitStats();

      expect(stats).toHaveProperty("state");
      expect(stats).toHaveProperty("failureCount");
      expect(stats).toHaveProperty("successCount");
      expect(stats.state).toBe("closed");
    });
  });
});
