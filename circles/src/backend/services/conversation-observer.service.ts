/**
 * Conversation Observer Service
 *
 * Tracks agent-to-agent conversation state for graph visualization.
 * Provides methods to track conversation lifecycle, turns, thinking states,
 * and judge decisions without impacting the business logic.
 *
 * This service is designed to be optionally injected into InterviewFlowService.
 */

import {
  OBSERVER_REDIS_KEYS,
  CONVERSATION_CONFIG,
} from "../config/observer.config.js";
import { getEventBus } from "../infrastructure/observer/index.js";
import type {
  ConversationTurn,
  ConversationState,
  JudgeDecision,
} from "../infrastructure/observer/types.js";
import { getRedisClient } from "../infrastructure/redis.js";

export class ConversationObserverService {
  private readonly redis = getRedisClient();

  /**
   * Initialize a new conversation for a mission
   */
  async initConversation(mission: {
    missionId: string;
    ownerUserId: string;
    visitorUserId: string;
    ownerCircleId: string;
    timestamp: number;
  }): Promise<void> {
    try {
      const missionKey = OBSERVER_REDIS_KEYS.conversationMission(
        mission.missionId,
      );
      const stateKey = OBSERVER_REDIS_KEYS.conversationState(mission.missionId);
      const ownerIndexKey = OBSERVER_REDIS_KEYS.conversationsByUser(
        mission.ownerUserId,
      );
      const visitorIndexKey = OBSERVER_REDIS_KEYS.conversationsByUser(
        mission.visitorUserId,
      );
      const activeIndexKey = OBSERVER_REDIS_KEYS.conversationsActive();

      const ttl = CONVERSATION_CONFIG.conversationTtl;

      const pipeline = this.redis.pipeline();

      // Store conversation metadata
      pipeline.hset(missionKey, {
        missionId: mission.missionId,
        ownerUserId: mission.ownerUserId,
        visitorUserId: mission.visitorUserId,
        ownerCircleId: mission.ownerCircleId,
        status: "pending",
        turnCount: "0",
        createdAt: String(mission.timestamp),
        expiresAt: String(mission.timestamp + ttl * 1000),
      });
      pipeline.expire(missionKey, ttl);

      // Initialize conversation state
      pipeline.hset(stateKey, {
        isThinking: "false",
        currentSpeaker: "",
        lastTurnTimestamp: String(mission.timestamp),
      });
      pipeline.expire(stateKey, ttl);

      // Add to indexes
      pipeline.sadd(ownerIndexKey, mission.missionId);
      pipeline.expire(ownerIndexKey, ttl);
      pipeline.sadd(visitorIndexKey, mission.missionId);
      pipeline.expire(visitorIndexKey, ttl);
      pipeline.sadd(activeIndexKey, mission.missionId);
      pipeline.expire(activeIndexKey, ttl);

      await pipeline.exec();

      // Emit event
      const eventBus = getEventBus();
      eventBus.emit({
        type: "conversation.started",
        userId: mission.ownerUserId,
        relatedUserId: mission.visitorUserId,
        circleId: mission.ownerCircleId,
        metadata: {
          missionId: mission.missionId,
          timestamp: mission.timestamp,
        },
      });
    } catch (error) {
      console.error("[ConversationObserver] Failed to init conversation", {
        error,
        missionId: mission.missionId,
      });
    }
  }

  /**
   * Mark agent as thinking (typing indicator)
   */
  async startThinking(
    missionId: string,
    speaker: "owner" | "visitor",
  ): Promise<void> {
    try {
      const stateKey = OBSERVER_REDIS_KEYS.conversationState(missionId);
      const thinkingKey = OBSERVER_REDIS_KEYS.conversationThinking(
        missionId,
        speaker,
      );
      const missionKey = OBSERVER_REDIS_KEYS.conversationMission(missionId);

      const timestamp = Date.now();

      const pipeline = this.redis.pipeline();

      // Update state
      pipeline.hset(stateKey, {
        isThinking: "true",
        currentSpeaker: speaker,
        thinkingStartedAt: String(timestamp),
      });

      // Set thinking indicator with TTL
      pipeline.set(
        thinkingKey,
        timestamp.toString(),
        "EX",
        CONVERSATION_CONFIG.thinkingTtl,
      );

      // Extend conversation TTL
      pipeline.expire(missionKey, CONVERSATION_CONFIG.conversationTtl);
      pipeline.expire(stateKey, CONVERSATION_CONFIG.conversationTtl);

      await pipeline.exec();

      // Emit event
      const eventBus = getEventBus();
      const mission = await this.redis.hgetall(missionKey);

      eventBus.emit({
        type: "conversation.thinking_started",
        userId:
          speaker === "owner" ? mission.ownerUserId! : mission.visitorUserId!,
        relatedUserId:
          speaker === "owner" ? mission.visitorUserId! : mission.ownerUserId!,
        circleId: mission.ownerCircleId,
        metadata: {
          missionId,
          speaker,
          timestamp,
        },
      });
    } catch (error) {
      console.error("[ConversationObserver] Failed to start thinking", {
        error,
        missionId,
        speaker,
      });
    }
  }

  /**
   * Add a conversation turn
   */
  async addTurn(missionId: string, turn: ConversationTurn): Promise<void> {
    try {
      const missionKey = OBSERVER_REDIS_KEYS.conversationMission(missionId);
      const turnsKey = OBSERVER_REDIS_KEYS.conversationTurns(missionId);
      const stateKey = OBSERVER_REDIS_KEYS.conversationState(missionId);
      const thinkingKey = OBSERVER_REDIS_KEYS.conversationThinking(
        missionId,
        turn.speaker,
      );

      const pipeline = this.redis.pipeline();

      // Add turn to list
      pipeline.rpush(turnsKey, JSON.stringify(turn));

      // Update turn count
      pipeline.hincrby(missionKey, "turnCount", 1);

      // Clear thinking state
      pipeline.del(thinkingKey);
      pipeline.hset(stateKey, {
        isThinking: "false",
        lastTurnTimestamp: String(turn.timestamp),
        lastSpeaker: turn.speaker,
      });

      // Extend TTLs
      const ttl = CONVERSATION_CONFIG.conversationTtl;
      pipeline.expire(missionKey, ttl);
      pipeline.expire(turnsKey, ttl);
      pipeline.expire(stateKey, ttl);

      await pipeline.exec();

      // Emit events
      const eventBus = getEventBus();
      const mission = await this.redis.hgetall(missionKey);

      // Emit turn completed event
      eventBus.emit({
        type: "conversation.turn_completed",
        userId:
          turn.speaker === "owner"
            ? mission.ownerUserId!
            : mission.visitorUserId!,
        relatedUserId:
          turn.speaker === "owner"
            ? mission.visitorUserId!
            : mission.ownerUserId!,
        circleId: mission.ownerCircleId,
        metadata: {
          missionId,
          speaker: turn.speaker,
          turnNumber: turn.turnNumber,
          message: turn.message,
          thinkingDuration: turn.thinkingDuration,
          timestamp: turn.timestamp,
        },
      });

      // Emit thinking completed event
      if (turn.thinkingDuration) {
        eventBus.emit({
          type: "conversation.thinking_completed",
          userId:
            turn.speaker === "owner"
              ? mission.ownerUserId!
              : mission.visitorUserId!,
          relatedUserId:
            turn.speaker === "owner"
              ? mission.visitorUserId!
              : mission.ownerUserId!,
          circleId: mission.ownerCircleId,
          metadata: {
            missionId,
            speaker: turn.speaker,
            duration: turn.thinkingDuration,
            timestamp: turn.timestamp,
          },
        });
      }
    } catch (error) {
      console.error("[ConversationObserver] Failed to add turn", {
        error,
        missionId,
        turnNumber: turn.turnNumber,
      });
    }
  }

  /**
   * Store judge decision
   */
  async storeJudgeDecision(
    missionId: string,
    decision: JudgeDecision,
  ): Promise<void> {
    try {
      const missionKey = OBSERVER_REDIS_KEYS.conversationMission(missionId);

      await this.redis.hset(missionKey, {
        judgeApproved: String(decision.approved),
        judgeScore: String(decision.score),
        judgeReasoning: decision.reasoning,
        judgeTimestamp: String(decision.timestamp),
      });

      await this.redis.expire(missionKey, CONVERSATION_CONFIG.conversationTtl);

      // Emit event
      const eventBus = getEventBus();
      const mission = await this.redis.hgetall(missionKey);

      eventBus.emit({
        type: "conversation.judge_decision",
        userId: mission.ownerUserId!,
        relatedUserId: mission.visitorUserId!,
        circleId: mission.ownerCircleId,
        metadata: {
          missionId,
          approved: decision.approved,
          score: decision.score,
          reasoning: decision.reasoning,
          timestamp: decision.timestamp,
        },
      });
    } catch (error) {
      console.error("[ConversationObserver] Failed to store judge decision", {
        error,
        missionId,
      });
    }
  }

  /**
   * Complete a conversation
   */
  async completeConversation(
    missionId: string,
    status: "completed" | "failed",
  ): Promise<void> {
    try {
      const missionKey = OBSERVER_REDIS_KEYS.conversationMission(missionId);
      const stateKey = OBSERVER_REDIS_KEYS.conversationState(missionId);
      const activeIndexKey = OBSERVER_REDIS_KEYS.conversationsActive();

      const timestamp = Date.now();

      const pipeline = this.redis.pipeline();

      // Update status
      pipeline.hset(missionKey, {
        status,
        completedAt: String(timestamp),
      });

      pipeline.hset(stateKey, {
        isThinking: "false",
        currentSpeaker: "",
      });

      // Remove from active index
      pipeline.srem(activeIndexKey, missionId);

      // Keep data for TTL period
      const ttl = CONVERSATION_CONFIG.conversationTtl;
      pipeline.expire(missionKey, ttl);
      pipeline.expire(stateKey, ttl);

      await pipeline.exec();

      // Emit event
      const eventBus = getEventBus();
      const mission = await this.redis.hgetall(missionKey);

      eventBus.emit({
        type: "conversation.completed",
        userId: mission.ownerUserId!,
        relatedUserId: mission.visitorUserId!,
        circleId: mission.ownerCircleId,
        metadata: {
          missionId,
          status,
          turnCount: Number(mission.turnCount) || 0,
          timestamp,
          duration: timestamp - Number(mission.createdAt || 0),
        },
      });
    } catch (error) {
      console.error("[ConversationObserver] Failed to complete conversation", {
        error,
        missionId,
        status,
      });
    }
  }

  /**
   * Get conversation state (for debugging/monitoring)
   */
  async getConversationState(
    missionId: string,
  ): Promise<ConversationState | null> {
    try {
      const missionKey = OBSERVER_REDIS_KEYS.conversationMission(missionId);
      const stateKey = OBSERVER_REDIS_KEYS.conversationState(missionId);

      const [missionData, stateData] = await Promise.all([
        this.redis.hgetall(missionKey),
        this.redis.hgetall(stateKey),
      ]);

      if (!missionData.missionId) {
        return null;
      }

      const status = missionData.status || "pending";
      const currentSpeaker = stateData.currentSpeaker || undefined;

      // Validate and parse status
      let validatedStatus: ConversationState["status"] = "pending";
      if (
        status === "pending" ||
        status === "in_progress" ||
        status === "completed" ||
        status === "failed"
      ) {
        validatedStatus = status;
      }

      // Validate and parse currentSpeaker
      let validatedSpeaker: "owner" | "visitor" | undefined;
      if (currentSpeaker === "owner" || currentSpeaker === "visitor") {
        validatedSpeaker = currentSpeaker;
      }

      return {
        missionId: missionData.missionId,
        ownerUserId: missionData.ownerUserId ?? "",
        visitorUserId: missionData.visitorUserId ?? "",
        ownerCircleId: missionData.ownerCircleId ?? "",
        status: validatedStatus,
        turnCount: Number(missionData.turnCount) || 0,
        currentSpeaker: validatedSpeaker,
        isThinking: stateData.isThinking === "true",
        createdAt: Number(missionData.createdAt) || 0,
        updatedAt: Number(stateData.lastTurnTimestamp) || 0,
        completedAt: missionData.completedAt
          ? Number(missionData.completedAt)
          : undefined,
      };
    } catch (error) {
      console.error("[ConversationObserver] Failed to get conversation state", {
        error,
        missionId,
      });
      return null;
    }
  }

  /**
   * Get conversation turns
   */
  async getConversationTurns(missionId: string): Promise<ConversationTurn[]> {
    try {
      const turnsKey = OBSERVER_REDIS_KEYS.conversationTurns(missionId);
      const turns = await this.redis.lrange(turnsKey, 0, -1);

      return turns.map((turnJson): ConversationTurn => JSON.parse(turnJson));
    } catch (error) {
      console.error("[ConversationObserver] Failed to get conversation turns", {
        error,
        missionId,
      });
      return [];
    }
  }

  /**
   * Get active conversations for a user
   */
  async getActiveConversations(userId: string): Promise<string[]> {
    try {
      const indexKey = OBSERVER_REDIS_KEYS.conversationsByUser(userId);
      return await this.redis.smembers(indexKey);
    } catch (error) {
      console.error(
        "[ConversationObserver] Failed to get active conversations",
        {
          error,
          userId,
        },
      );
      return [];
    }
  }
}

/**
 * Singleton export
 */
export const conversationObserverService = new ConversationObserverService();
