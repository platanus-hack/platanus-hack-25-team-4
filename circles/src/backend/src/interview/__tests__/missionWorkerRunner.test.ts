import { describe, it, expect, vi, beforeEach } from "vitest";

import {
  createMissionJobHandler,
  createDefaultMissionJobHandler,
  type MissionJob,
} from "../missionWorker.js";
import type { InterviewMission, InterviewMissionResult } from "../types.js";

// Mock modules
vi.mock("../agentsRuntime.js", () => ({
  BedrockInterviewAgentsRuntime: vi.fn(() => ({
    runOwnerTurn: vi.fn(),
    runVisitorTurn: vi.fn(),
  })),
}));

vi.mock("../judge.js", () => ({
  BedrockInterviewJudge: vi.fn(() => ({
    judge: vi.fn(),
  })),
}));

vi.mock("../notificationGateway.js", () => ({
  LoggingNotificationGateway: vi.fn(() => ({
    notifySuccessfulInteraction: vi.fn(),
  })),
}));

vi.mock("../interviewFlowService.js", () => ({
  InterviewFlowService: vi.fn(),
}));

// Create a mock factory that returns both the interface methods and vitest mock utilities
function createMockFlowService() {
  const mockRunMission = vi.fn();
  return {
    runMission: mockRunMission,
  };
}

describe("MissionJobHandler", () => {
  let mockFlowService: ReturnType<typeof createMockFlowService>;

  const createMockMission = (): InterviewMission => ({
    mission_id: "test-mission-123",
    owner_user_id: "owner-user-1",
    visitor_user_id: "visitor-user-2",
    owner_profile: {
      id: "owner-user-1",
      display_name: "Alice",
      motivations_and_goals: {
        primary_goal: "Meet fellow developers",
      },
    },
    visitor_profile: {
      id: "visitor-user-2",
      display_name: "Bob",
      motivations_and_goals: {
        primary_goal: "Networking",
      },
    },
    owner_circle: {
      id: "circle-1",
      objective_text: "Coffee meetup for developers",
      radius_m: 500,
      time_window: "This week, mornings",
    },
    context: {
      approximate_time_iso: new Date().toISOString(),
      approximate_distance_m: 250,
    },
  });

  const createMockJob = (mission: InterviewMission): MissionJob => ({
    id: "job-123",
    data: mission,
  });

  beforeEach(() => {
    vi.clearAllMocks();
    mockFlowService = createMockFlowService();
  });

  describe("createMissionJobHandler", () => {
    it("creates a job handler function", () => {
      const handler = createMissionJobHandler(mockFlowService);

      expect(handler).toBeInstanceOf(Function);
    });

    it("handler calls flowService.runMission with mission data", async () => {
      const mission = createMockMission();
      const job = createMockJob(mission);

      const mockResult: InterviewMissionResult = {
        mission_id: mission.mission_id,
        transcript: [],
        judge_decision: {
          should_notify: false,
        },
      };

      mockFlowService.runMission.mockResolvedValue(mockResult);

      const handler = createMissionJobHandler(
        mockFlowService,
      );
      await handler(job);

      expect(mockFlowService.runMission).toHaveBeenCalledTimes(1);
      expect(mockFlowService.runMission).toHaveBeenCalledWith(mission);
    });

    it("handler processes job with correct mission data", async () => {
      const mission = createMockMission();
      const job = createMockJob(mission);

      const handler = createMissionJobHandler(
        mockFlowService,
      );
      await handler(job);

      expect(mockFlowService.runMission.mock.calls).toHaveLength(1);
      const callArg = mockFlowService.runMission.mock.calls[0]?.[0];
      expect(callArg).toBe(mission);
      expect(callArg?.mission_id).toBe("test-mission-123");
      expect(callArg?.owner_circle.objective_text).toBe(
        "Coffee meetup for developers",
      );
    });

    it("handler propagates errors from flowService", async () => {
      const mission = createMockMission();
      const job = createMockJob(mission);

      const testError = new Error("Interview flow failed");
      mockFlowService.runMission.mockRejectedValue(testError);

      const handler = createMissionJobHandler(
        mockFlowService,
      );

      await expect(handler(job)).rejects.toThrow("Interview flow failed");
    });

    it("handler handles multiple jobs sequentially", async () => {
      const mission1 = createMockMission();
      const mission2 = {
        ...createMockMission(),
        mission_id: "test-mission-456",
      };

      const job1 = createMockJob(mission1);
      const job2 = createMockJob(mission2);

      const handler = createMissionJobHandler(
        mockFlowService,
      );

      await handler(job1);
      await handler(job2);

      expect(mockFlowService.runMission).toHaveBeenCalledTimes(2);
      expect(mockFlowService.runMission).toHaveBeenNthCalledWith(1, mission1);
      expect(mockFlowService.runMission).toHaveBeenNthCalledWith(2, mission2);
    });
  });

  describe("createDefaultMissionJobHandler", () => {
    it("creates a handler without throwing", () => {
      expect(() => createDefaultMissionJobHandler()).not.toThrow();
    });

    it("returns a function", () => {
      const handler = createDefaultMissionJobHandler();
      expect(handler).toBeInstanceOf(Function);
    });

    it("created handler is a callable function", () => {
      const handler = createDefaultMissionJobHandler();
      expect(typeof handler).toBe("function");
    });
  });

  describe("Job ID and data extraction", () => {
    it("handler uses job.id when processing", async () => {
      const mission = createMockMission();
      const job: MissionJob = {
        id: "custom-job-id-789",
        data: mission,
      };

      const handler = createMissionJobHandler(
        mockFlowService,
      );
      await handler(job);

      // Verify the job was processed (mission passed to flowService)
      expect(mockFlowService.runMission).toHaveBeenCalledWith(mission);
    });

    it("handler extracts mission data from job", async () => {
      const mission = createMockMission();
      mission.owner_profile.display_name = "Charlie";
      mission.visitor_profile.display_name = "Dana";

      const job = createMockJob(mission);

      const handler = createMissionJobHandler(
        mockFlowService,
      );
      await handler(job);

      expect(mockFlowService.runMission.mock.calls).toHaveLength(1);
      const calledMission = mockFlowService.runMission.mock.calls[0]?.[0];
      expect(calledMission?.owner_profile.display_name).toBe("Charlie");
      expect(calledMission?.visitor_profile.display_name).toBe("Dana");
    });
  });

  describe("Error handling", () => {
    it("handler throws when flowService fails", async () => {
      const mission = createMockMission();
      const job = createMockJob(mission);

      mockFlowService.runMission.mockRejectedValue(
        new Error("Service unavailable"),
      );

      const handler = createMissionJobHandler(
        mockFlowService,
      );

      await expect(handler(job)).rejects.toThrow("Service unavailable");
    });

    it("handler does not catch errors", async () => {
      const mission = createMockMission();
      const job = createMockJob(mission);

      const customError = new Error("Custom error");
      mockFlowService.runMission.mockRejectedValue(customError);

      const handler = createMissionJobHandler(
        mockFlowService,
      );

      let caughtError;
      try {
        await handler(job);
      } catch (error) {
        caughtError = error;
      }

      expect(caughtError).toBe(customError);
    });
  });

  describe("Integration behavior", () => {
    it("handler can process complete mission with all fields", async () => {
      const mission: InterviewMission = {
        mission_id: "integration-mission-1",
        owner_user_id: "owner-123",
        visitor_user_id: "visitor-456",
        owner_profile: {
          id: "owner-123",
          display_name: "Emma",
          motivations_and_goals: {
            primary_goal: "Find collaborators for open source projects",
          },
          conversation_micro_preferences: {
            preferred_opener_style: "casual and friendly",
          },
        },
        visitor_profile: {
          id: "visitor-456",
          display_name: "Frank",
          motivations_and_goals: {
            primary_goal: "Learn from experienced developers",
          },
        },
        owner_circle: {
          id: "circle-integration-1",
          objective_text: "Weekly meetup for OSS contributors",
          radius_m: 1000,
          time_window: "Weekends, afternoons",
        },
        context: {
          approximate_time_iso: new Date().toISOString(),
          approximate_distance_m: 500,
        },
      };

      const job = createMockJob(mission);

      const handler = createMissionJobHandler(
        mockFlowService,
      );
      await handler(job);

      expect(mockFlowService.runMission).toHaveBeenCalledWith(
        expect.objectContaining({
          mission_id: "integration-mission-1",
          owner_circle: expect.objectContaining({
            objective_text: "Weekly meetup for OSS contributors",
          }),
        }),
      );
    });
  });
});
