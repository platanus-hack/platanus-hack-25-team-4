import { describe, it, expect, beforeEach, vi } from "vitest";

import { Observe, observe } from "../../infrastructure/observer/observable.js";

interface MockEventBus {
  emit: ReturnType<typeof vi.fn>;
  getBufferSize: ReturnType<typeof vi.fn>;
  getCircuitStats: ReturnType<typeof vi.fn>;
  forceFlush: ReturnType<typeof vi.fn>;
}

// Mock EventBus
const mockEventBus: MockEventBus = {
  emit: vi.fn(),
  getBufferSize: vi.fn(() => 0),
  getCircuitStats: vi.fn(() => ({
    state: "closed" as const,
    failureCount: 0,
    successCount: 0,
    lastFailureTime: 0,
  })),
  forceFlush: vi.fn(),
};

vi.mock("../../infrastructure/observer/event-bus.js", () => ({
  getEventBus: () => mockEventBus,
}));

describe("Observable Decorator", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("@Observe decorator", () => {
    it("should emit event on successful method execution", async () => {
      class TestService {
        // @ts-expect-error - TypeScript has limitations with experimental decorators that modify PropertyDescriptor
        @Observe({
          eventType: "location.updated",
          extractUserId: (args) => String(args[0]),
        })
        async updateLocation(
          _userId: string,
          _lat: number,
          _lon: number,
        ): Promise<boolean> {
          return true;
        }
      }

      const service = new TestService();
      await service.updateLocation("user-1", 40.7128, -74.006);

      expect(mockEventBus.emit).toHaveBeenCalledWith({
        type: "location.updated",
        userId: "user-1",
        relatedUserId: undefined,
        circleId: undefined,
        metadata: { result: true },
      });
    });

    it("should extract relatedUserId when provided", async () => {
      class TestService {
        // @ts-expect-error - TypeScript has limitations with experimental decorators that modify PropertyDescriptor
        @Observe({
          eventType: "collision.detected",
          extractUserId: (args) => String(args[0]),
          extractRelatedUserId: (args) => String(args[1]),
        })
        async detectCollision(
          _userId1: string,
          _userId2: string,
        ): Promise<void> {}
      }

      const service = new TestService();
      await service.detectCollision("user-1", "user-2");

      expect(mockEventBus.emit).toHaveBeenCalledWith({
        type: "collision.detected",
        userId: "user-1",
        relatedUserId: "user-2",
        circleId: undefined,
        metadata: { result: undefined },
      });
    });

    it("should extract circleId when provided", async () => {
      class TestService {
        // @ts-expect-error - TypeScript has limitations with experimental decorators that modify PropertyDescriptor
        @Observe({
          eventType: "agent_match.mission_created",
          extractUserId: (args) => String(args[0]),
          extractCircleId: (args) => String(args[1]),
        })
        async createMission(
          _userId: string,
          _circleId: string,
        ): Promise<string> {
          return "mission-id";
        }
      }

      const service = new TestService();
      await service.createMission("user-1", "circle-1");

      expect(mockEventBus.emit).toHaveBeenCalledWith({
        type: "agent_match.mission_created",
        userId: "user-1",
        relatedUserId: undefined,
        circleId: "circle-1",
        metadata: { result: "mission-id" },
      });
    });

    it("should use custom metadata builder", async () => {
      class TestService {
        // @ts-expect-error - TypeScript has limitations with experimental decorators that modify PropertyDescriptor
        @Observe({
          eventType: "location.updated",
          extractUserId: (args) => String(args[0]),
          buildMetadata: (args, result) => ({
            latitude: args[1],
            longitude: args[2],
            accuracy: args[3],
            success: result,
          }),
        })
        async updateLocation(
          _userId: string,
          _lat: number,
          _lon: number,
          _accuracy: number,
        ): Promise<boolean> {
          return true;
        }
      }

      const service = new TestService();
      await service.updateLocation("user-1", 40.7128, -74.006, 10);

      expect(mockEventBus.emit).toHaveBeenCalledWith({
        type: "location.updated",
        userId: "user-1",
        relatedUserId: undefined,
        circleId: undefined,
        metadata: {
          latitude: 40.7128,
          longitude: -74.006,
          accuracy: 10,
          success: true,
        },
      });
    });

    it("should not emit event on error by default", async () => {
      class TestService {
        // @ts-expect-error - TypeScript has limitations with experimental decorators that modify PropertyDescriptor
        @Observe({
          eventType: "location.updated",
          extractUserId: (args) => String(args[0]),
        })
        async updateLocation(_userId: string): Promise<void> {
          throw new Error("Update failed");
        }
      }

      const service = new TestService();

      await expect(service.updateLocation("user-1")).rejects.toThrow(
        "Update failed",
      );
      expect(mockEventBus.emit).not.toHaveBeenCalled();
    });

    it("should emit event on error when configured", async () => {
      class TestService {
        // @ts-expect-error - TypeScript has limitations with experimental decorators that modify PropertyDescriptor
        @Observe({
          eventType: "location.updated",
          extractUserId: (args) => String(args[0]),
          emitOnError: true,
        })
        async updateLocation(_userId: string): Promise<void> {
          throw new Error("Update failed");
        }
      }

      const service = new TestService();

      await expect(service.updateLocation("user-1")).rejects.toThrow(
        "Update failed",
      );
      expect(mockEventBus.emit).toHaveBeenCalledWith({
        type: "location.updated",
        userId: "user-1",
        relatedUserId: undefined,
        circleId: undefined,
        metadata: { result: "Error: Update failed" },
      });
    });

    it("should preserve original method return value", async () => {
      class TestService {
        // @ts-expect-error - TypeScript has limitations with experimental decorators that modify PropertyDescriptor
        @Observe({
          eventType: "match.created",
          extractUserId: (args) => String(args[0]),
        })
        async createMatch(
          _userId: string,
        ): Promise<{ matchId: string; status: string }> {
          return { matchId: "match-1", status: "pending" };
        }
      }

      const service = new TestService();
      const result = await service.createMatch("user-1");

      expect(result).toEqual({ matchId: "match-1", status: "pending" });
    });

    it("should handle methods with no return value", async () => {
      class TestService {
        // @ts-expect-error - TypeScript has limitations with experimental decorators that modify PropertyDescriptor
        @Observe({
          eventType: "collision.expired",
          extractUserId: (args) => String(args[0]),
        })
        async expireCollision(_userId: string): Promise<void> {
          // No return
        }
      }

      const service = new TestService();
      await service.expireCollision("user-1");

      expect(mockEventBus.emit).toHaveBeenCalledWith({
        type: "collision.expired",
        userId: "user-1",
        relatedUserId: undefined,
        circleId: undefined,
        metadata: { result: undefined },
      });
    });

    it("should not emit if userId extraction fails", async () => {
      class TestService {
        // @ts-expect-error - TypeScript has limitations with experimental decorators that modify PropertyDescriptor
        @Observe({
          eventType: "location.updated",
          extractUserId: () => {
            return "";
          },
        })
        async updateLocation(_data: {
          lat: number;
          lon: number;
        }): Promise<void> {}
      }

      const service = new TestService();
      await service.updateLocation({ lat: 40.7128, lon: -74.006 });

      // Should not emit when userId extraction fails
      expect(mockEventBus.emit).not.toHaveBeenCalled();
    });

    it("should handle decorator errors gracefully", async () => {
      class TestService {
        // @ts-expect-error - TypeScript has limitations with experimental decorators that modify PropertyDescriptor
        @Observe({
          eventType: "location.updated",
          extractUserId: () => {
            throw new Error("Extraction failed");
          },
        })
        async updateLocation(_userId: string): Promise<string> {
          return "success";
        }
      }

      const service = new TestService();
      const result = await service.updateLocation("user-1");

      // Method should still execute and return
      expect(result).toBe("success");

      // Event should not be emitted due to extraction error
      expect(mockEventBus.emit).not.toHaveBeenCalled();
    });
  });

  describe("observe functional API", () => {
    it("should wrap function and emit event", async () => {
      const originalFn = async (..._args: unknown[]) => {
        return { success: true };
      };

      const observedFn = observe(
        {
          eventType: "location.updated",
          extractUserId: (args) => String(args[0]),
          buildMetadata: (args) => ({
            latitude: args[1],
            longitude: args[2],
          }),
        },
        originalFn,
      );

      const result = await observedFn("user-1", 40.7128, -74.006);

      expect(result).toEqual({ success: true });
      expect(mockEventBus.emit).toHaveBeenCalledWith({
        type: "location.updated",
        userId: "user-1",
        relatedUserId: undefined,
        circleId: undefined,
        metadata: {
          latitude: 40.7128,
          longitude: -74.006,
        },
      });
    });

    it("should handle errors in functional API", async () => {
      const originalFn = async (..._args: unknown[]) => {
        throw new Error("Function failed");
      };

      const observedFn = observe(
        {
          eventType: "location.updated",
          extractUserId: (args) => String(args[0]),
          emitOnError: true,
        },
        originalFn,
      );

      await expect(observedFn("user-1")).rejects.toThrow("Function failed");
      expect(mockEventBus.emit).toHaveBeenCalled();
    });
  });

  describe("multiple decorators", () => {
    it("should handle class with multiple decorated methods", async () => {
      class TestService {
        // @ts-expect-error - TypeScript has limitations with experimental decorators that modify PropertyDescriptor
        @Observe({
          eventType: "location.updated",
          extractUserId: (args) => String(args[0]),
        })
        async updateLocation(_userId: string): Promise<void> {}

        // @ts-expect-error - TypeScript has limitations with experimental decorators that modify PropertyDescriptor
        @Observe({
          eventType: "collision.detected",
          extractUserId: (args) => String(args[0]),
        })
        async detectCollision(_userId: string): Promise<void> {}
      }

      const service = new TestService();

      await service.updateLocation("user-1");
      expect(mockEventBus.emit).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "location.updated",
          userId: "user-1",
        }),
      );

      vi.clearAllMocks();

      await service.detectCollision("user-2");
      expect(mockEventBus.emit).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "collision.detected",
          userId: "user-2",
        }),
      );
    });
  });
});
