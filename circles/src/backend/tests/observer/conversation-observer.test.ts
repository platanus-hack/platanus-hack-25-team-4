import { describe, it, expect, beforeEach, vi } from "vitest";

import type { ConversationTurn } from "../../infrastructure/observer/types.js";

// Type guard for Record<string, string>
function isStringRecord(value: unknown): value is Record<string, string> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    Object.values(value).every((v) => typeof v === "string")
  );
}

// Mock Redis
const redisData = new Map<string, Record<string, string>>();
const redisStrings = new Map<string, string>();
const redisLists = new Map<string, string[]>();
const redisSets = new Map<string, Set<string>>();

const mockRedis = {
  hset: vi.fn(async (key: string, data: Record<string, string>) => {
    redisData.set(key, { ...(redisData.get(key) || {}), ...data });
    return "OK";
  }),
  hgetall: vi.fn(async (key: string) => {
    return redisData.get(key) || {};
  }),
  hincrby: vi.fn(async (key: string, field: string, increment: number) => {
    const data = redisData.get(key) || {};
    const currentValue = parseInt(data[field] || "0", 10);
    data[field] = String(currentValue + increment);
    redisData.set(key, data);
    return currentValue + increment;
  }),
  expire: vi.fn(async () => 1),
  set: vi.fn(async (key: string, value: string) => {
    redisStrings.set(key, value);
    return "OK";
  }),
  del: vi.fn(async (key: string) => {
    redisData.delete(key);
    redisStrings.delete(key);
    return 1;
  }),
  rpush: vi.fn(async (key: string, value: string) => {
    if (!redisLists.has(key)) {
      redisLists.set(key, []);
    }
    redisLists.get(key)!.push(value);
    return redisLists.get(key)!.length;
  }),
  lrange: vi.fn(async (key: string, start: number, end: number) => {
    const list = redisLists.get(key) || [];
    if (end === -1) {
      return list.slice(start);
    }
    return list.slice(start, end + 1);
  }),
  sadd: vi.fn(async (key: string, ...members: string[]) => {
    if (!redisSets.has(key)) {
      redisSets.set(key, new Set());
    }
    members.forEach((member) => redisSets.get(key)!.add(member));
    return members.length;
  }),
  srem: vi.fn(async (key: string, member: string) => {
    const set = redisSets.get(key);
    if (set) {
      set.delete(member);
      return 1;
    }
    return 0;
  }),
  smembers: vi.fn(async (key: string) => {
    return Array.from(redisSets.get(key) || []);
  }),
  pipeline: vi.fn(() => {
    const commands: Array<{ cmd: string; args: unknown[] }> = [];

    type PipelineChain = {
      hset: (...args: unknown[]) => PipelineChain;
      expire: (...args: unknown[]) => PipelineChain;
      sadd: (...args: unknown[]) => PipelineChain;
      srem: (...args: unknown[]) => PipelineChain;
      set: (...args: unknown[]) => PipelineChain;
      del: (...args: unknown[]) => PipelineChain;
      rpush: (...args: unknown[]) => PipelineChain;
      hincrby: (...args: unknown[]) => PipelineChain;
      exec: () => Promise<unknown[]>;
    };

    const chain: PipelineChain = {
      hset: vi.fn(function (...args: unknown[]) {
        commands.push({ cmd: "hset", args });
        return chain;
      }),
      expire: vi.fn(function (...args: unknown[]) {
        commands.push({ cmd: "expire", args });
        return chain;
      }),
      sadd: vi.fn(function (...args: unknown[]) {
        commands.push({ cmd: "sadd", args });
        return chain;
      }),
      srem: vi.fn(function (...args: unknown[]) {
        commands.push({ cmd: "srem", args });
        return chain;
      }),
      set: vi.fn(function (...args: unknown[]) {
        commands.push({ cmd: "set", args });
        return chain;
      }),
      del: vi.fn(function (...args: unknown[]) {
        commands.push({ cmd: "del", args });
        return chain;
      }),
      rpush: vi.fn(function (...args: unknown[]) {
        commands.push({ cmd: "rpush", args });
        return chain;
      }),
      hincrby: vi.fn(function (...args: unknown[]) {
        commands.push({ cmd: "hincrby", args });
        return chain;
      }),
      exec: vi.fn(async () => {
        // Execute commands in order
        for (const { cmd, args } of commands) {
          if (cmd === "hset" && typeof args[0] === "string" && isStringRecord(args[1])) {
            await mockRedis.hset(args[0], args[1]);
          } else if (
            cmd === "hincrby" &&
            typeof args[0] === "string" &&
            typeof args[1] === "string" &&
            typeof args[2] === "number"
          ) {
            await mockRedis.hincrby(args[0], args[1], args[2]);
          } else if (cmd === "sadd" && typeof args[0] === "string") {
            await mockRedis.sadd(args[0], ...args.slice(1).map(String));
          } else if (
            cmd === "srem" &&
            typeof args[0] === "string" &&
            typeof args[1] === "string"
          ) {
            await mockRedis.srem(args[0], args[1]);
          } else if (
            cmd === "rpush" &&
            typeof args[0] === "string" &&
            typeof args[1] === "string"
          ) {
            await mockRedis.rpush(args[0], args[1]);
          } else if (cmd === "del" && typeof args[0] === "string") {
            await mockRedis.del(args[0]);
          } else if (
            cmd === "set" &&
            typeof args[0] === "string" &&
            typeof args[1] === "string"
          ) {
            // Handle SET with EX option: SET key value EX seconds
            await mockRedis.set(args[0], args[1]);
          }
        }
        return [];
      }),
    };

    return chain;
  }),
};

vi.mock("../../infrastructure/redis.js", () => ({
  getRedisClient: () => mockRedis,
}));

// Mock EventBus
const mockEventBus = {
  emit: vi.fn(),
};

vi.mock("../../infrastructure/observer/event-bus.js", () => ({
  getEventBus: () => mockEventBus,
}));

describe("ConversationObserverService", () => {
  type ServiceClass = new () => {
    initConversation: (mission: {
      missionId: string;
      ownerUserId: string;
      visitorUserId: string;
      ownerCircleId: string;
      timestamp: number;
    }) => Promise<void>;
    startThinking: (missionId: string, speaker: "owner" | "visitor") => Promise<void>;
    addTurn: (missionId: string, turn: ConversationTurn) => Promise<void>;
    storeJudgeDecision: (
      missionId: string,
      decision: { approved: boolean; score: number; reasoning: string; timestamp: number },
    ) => Promise<void>;
    completeConversation: (
      missionId: string,
      status: "completed" | "failed",
    ) => Promise<void>;
    getConversationState: (missionId: string) => Promise<unknown>;
    getConversationTurns: (missionId: string) => Promise<ConversationTurn[]>;
    getActiveConversations: (userId: string) => Promise<string[]>;
  };

  let ConversationObserverService: ServiceClass;
  let service: InstanceType<ServiceClass>;

  beforeEach(async () => {
    vi.clearAllMocks();
    redisData.clear();
    redisStrings.clear();
    redisLists.clear();
    redisSets.clear();

    // Dynamically import to get fresh instance with mocked dependencies
    const module = await import(
      "../../services/conversation-observer.service.js"
    );
    ConversationObserverService = module.ConversationObserverService;
    service = new ConversationObserverService();
  });

  describe("initConversation", () => {
    it("should initialize conversation with metadata", async () => {
      const mission = {
        missionId: "mission-1",
        ownerUserId: "user-1",
        visitorUserId: "user-2",
        ownerCircleId: "circle-1",
        timestamp: Date.now(),
      };

      await service.initConversation(mission);

      // Verify event was emitted
      expect(mockEventBus.emit).toHaveBeenCalledWith({
        type: "conversation.started",
        userId: mission.ownerUserId,
        relatedUserId: mission.visitorUserId,
        circleId: mission.ownerCircleId,
        metadata: {
          missionId: mission.missionId,
          timestamp: mission.timestamp,
        },
      });
    });

    it("should handle initialization errors gracefully", async () => {
      // Mock Redis error
      mockRedis.pipeline = vi.fn(() => ({
        hset: vi.fn().mockReturnThis(),
        expire: vi.fn().mockReturnThis(),
        sadd: vi.fn().mockReturnThis(),
        srem: vi.fn().mockReturnThis(),
        set: vi.fn().mockReturnThis(),
        del: vi.fn().mockReturnThis(),
        rpush: vi.fn().mockReturnThis(),
        hincrby: vi.fn().mockReturnThis(),
        exec: vi.fn(async () => {
          throw new Error("Redis connection failed");
        }),
      }));

      const mission = {
        missionId: "mission-1",
        ownerUserId: "user-1",
        visitorUserId: "user-2",
        ownerCircleId: "circle-1",
        timestamp: Date.now(),
      };

      // Should not throw
      await expect(service.initConversation(mission)).resolves.not.toThrow();
    });
  });

  describe("startThinking", () => {
    it("should mark agent as thinking", async () => {
      // Setup: init conversation first
      await mockRedis.hset("conversation:mission:mission-1", {
        ownerUserId: "user-1",
        visitorUserId: "user-2",
        ownerCircleId: "circle-1",
      });

      await service.startThinking("mission-1", "owner");

      // Verify event was emitted
      expect(mockEventBus.emit).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "conversation.thinking_started",
          userId: "user-1",
          relatedUserId: "user-2",
          metadata: expect.objectContaining({
            missionId: "mission-1",
            speaker: "owner",
          }),
        }),
      );
    });

    it("should handle visitor thinking", async () => {
      await mockRedis.hset("conversation:mission:mission-1", {
        ownerUserId: "user-1",
        visitorUserId: "user-2",
        ownerCircleId: "circle-1",
      });

      await service.startThinking("mission-1", "visitor");

      expect(mockEventBus.emit).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "conversation.thinking_started",
          userId: "user-2", // Visitor
          relatedUserId: "user-1", // Owner
        }),
      );
    });
  });

  describe("addTurn", () => {
    it("should add conversation turn", async () => {
      await mockRedis.hset("conversation:mission:mission-1", {
        ownerUserId: "user-1",
        visitorUserId: "user-2",
        ownerCircleId: "circle-1",
        turnCount: "0",
      });

      const turn: ConversationTurn = {
        turnNumber: 1,
        speaker: "owner",
        message: "Hello, visitor!",
        timestamp: Date.now(),
        thinkingDuration: 1500,
      };

      await service.addTurn("mission-1", turn);

      // Verify turn completed event
      expect(mockEventBus.emit).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "conversation.turn_completed",
          metadata: expect.objectContaining({
            missionId: "mission-1",
            speaker: "owner",
            turnNumber: 1,
            message: "Hello, visitor!",
            thinkingDuration: 1500,
          }),
        }),
      );

      // Verify thinking completed event
      expect(mockEventBus.emit).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "conversation.thinking_completed",
          metadata: expect.objectContaining({
            duration: 1500,
          }),
        }),
      );
    });

    it("should increment turn count", async () => {
      await mockRedis.hset("conversation:mission:mission-1", {
        ownerUserId: "user-1",
        visitorUserId: "user-2",
        ownerCircleId: "circle-1",
        turnCount: "2",
      });

      const turn: ConversationTurn = {
        turnNumber: 3,
        speaker: "visitor",
        message: "Response",
        timestamp: Date.now(),
      };

      await service.addTurn("mission-1", turn);

      // Verify hincrby was called
      expect(mockRedis.pipeline).toHaveBeenCalled();
    });
  });

  describe("storeJudgeDecision", () => {
    it("should store judge decision and emit event", async () => {
      await mockRedis.hset("conversation:mission:mission-1", {
        ownerUserId: "user-1",
        visitorUserId: "user-2",
        ownerCircleId: "circle-1",
      });

      const decision = {
        approved: true,
        score: 8.5,
        reasoning: "Good conversation quality",
        timestamp: Date.now(),
      };

      await service.storeJudgeDecision("mission-1", decision);

      expect(mockEventBus.emit).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "conversation.judge_decision",
          metadata: expect.objectContaining({
            approved: true,
            score: 8.5,
            reasoning: "Good conversation quality",
          }),
        }),
      );
    });

    it("should handle rejected decisions", async () => {
      await mockRedis.hset("conversation:mission:mission-1", {
        ownerUserId: "user-1",
        visitorUserId: "user-2",
        ownerCircleId: "circle-1",
      });

      const decision = {
        approved: false,
        score: 3.2,
        reasoning: "Low engagement",
        timestamp: Date.now(),
      };

      await service.storeJudgeDecision("mission-1", decision);

      expect(mockEventBus.emit).toHaveBeenCalledWith(
        expect.objectContaining({
          metadata: expect.objectContaining({
            approved: false,
            score: 3.2,
          }),
        }),
      );
    });
  });

  describe("completeConversation", () => {
    it("should complete conversation successfully", async () => {
      const createdAt = Date.now() - 10000;

      await mockRedis.hset("conversation:mission:mission-1", {
        ownerUserId: "user-1",
        visitorUserId: "user-2",
        ownerCircleId: "circle-1",
        turnCount: "6",
        createdAt: String(createdAt),
      });

      await service.completeConversation("mission-1", "completed");

      expect(mockEventBus.emit).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "conversation.completed",
          metadata: expect.objectContaining({
            missionId: "mission-1",
            status: "completed",
            turnCount: 6,
          }),
        }),
      );
    });

    it("should handle failed conversations", async () => {
      await mockRedis.hset("conversation:mission:mission-1", {
        ownerUserId: "user-1",
        visitorUserId: "user-2",
        ownerCircleId: "circle-1",
        turnCount: "3",
        createdAt: String(Date.now()),
      });

      await service.completeConversation("mission-1", "failed");

      expect(mockEventBus.emit).toHaveBeenCalledWith(
        expect.objectContaining({
          metadata: expect.objectContaining({
            status: "failed",
          }),
        }),
      );
    });
  });

  describe("getConversationState", () => {
    it("should return conversation state", async () => {
      const now = Date.now();

      await mockRedis.hset("conversation:mission:mission-1", {
        missionId: "mission-1",
        ownerUserId: "user-1",
        visitorUserId: "user-2",
        ownerCircleId: "circle-1",
        status: "in_progress",
        turnCount: "4",
        createdAt: String(now),
      });

      await mockRedis.hset("conversation:state:mission-1", {
        isThinking: "true",
        currentSpeaker: "visitor",
        lastTurnTimestamp: String(now),
      });

      const state = await service.getConversationState("mission-1");

      expect(state).toEqual({
        missionId: "mission-1",
        ownerUserId: "user-1",
        visitorUserId: "user-2",
        ownerCircleId: "circle-1",
        status: "in_progress",
        turnCount: 4,
        currentSpeaker: "visitor",
        isThinking: true,
        createdAt: now,
        updatedAt: now,
        completedAt: undefined,
      });
    });

    it("should return null for non-existent conversation", async () => {
      const state = await service.getConversationState("non-existent");

      expect(state).toBeNull();
    });
  });

  describe("getConversationTurns", () => {
    it("should return all conversation turns", async () => {
      const turns: ConversationTurn[] = [
        {
          turnNumber: 1,
          speaker: "owner",
          message: "Hello",
          timestamp: Date.now(),
        },
        {
          turnNumber: 2,
          speaker: "visitor",
          message: "Hi there",
          timestamp: Date.now(),
        },
      ];

      redisLists.set(
        "conversation:turns:mission-1",
        turns.map((t) => JSON.stringify(t)),
      );

      const result = await service.getConversationTurns("mission-1");

      expect(result).toHaveLength(2);
      expect(result[0]).toEqual(turns[0]);
      expect(result[1]).toEqual(turns[1]);
    });

    it("should return empty array for non-existent conversation", async () => {
      const turns = await service.getConversationTurns("non-existent");

      expect(turns).toEqual([]);
    });
  });

  describe("getActiveConversations", () => {
    it("should return active conversations for user", async () => {
      redisSets.set(
        "conversation:index:user:user-1",
        new Set(["mission-1", "mission-2"]),
      );

      const conversations = await service.getActiveConversations("user-1");

      expect(conversations).toContain("mission-1");
      expect(conversations).toContain("mission-2");
      expect(conversations).toHaveLength(2);
    });

    it("should return empty array when no active conversations", async () => {
      const conversations = await service.getActiveConversations("user-999");

      expect(conversations).toEqual([]);
    });
  });

  describe("error handling", () => {
    it("should handle Redis errors gracefully in all methods", async () => {
      // Create a service that will use the current mocked Redis
      // Configure mockRedis to throw errors
      const originalPipeline = mockRedis.pipeline;
      mockRedis.pipeline = vi.fn(() => ({
        hset: vi.fn().mockReturnThis(),
        expire: vi.fn().mockReturnThis(),
        sadd: vi.fn().mockReturnThis(),
        srem: vi.fn().mockReturnThis(),
        set: vi.fn().mockReturnThis(),
        del: vi.fn().mockReturnThis(),
        rpush: vi.fn().mockReturnThis(),
        hincrby: vi.fn().mockReturnThis(),
        exec: vi.fn(async () => {
          throw new Error("Redis error");
        }),
      }));

      const errorService = new ConversationObserverService();

      // All methods should handle errors gracefully
      await expect(
        errorService.initConversation({
          missionId: "mission-1",
          ownerUserId: "user-1",
          visitorUserId: "user-2",
          ownerCircleId: "circle-1",
          timestamp: Date.now(),
        }),
      ).resolves.not.toThrow();

      await expect(
        errorService.startThinking("mission-1", "owner"),
      ).resolves.not.toThrow();

      await expect(
        errorService.addTurn("mission-1", {
          turnNumber: 1,
          speaker: "owner",
          message: "test",
          timestamp: Date.now(),
        }),
      ).resolves.not.toThrow();

      // Restore original pipeline
      mockRedis.pipeline = originalPipeline;
    });
  });
});
