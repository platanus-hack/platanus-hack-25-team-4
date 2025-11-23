/**
 * Observer System Configuration
 *
 * Central configuration for the graph visualization observer pattern.
 * Adjust these values to tune performance, memory usage, and fault tolerance.
 */

import type {
  EventBusConfig,
  CircuitBreakerConfig,
} from "../infrastructure/observer/types.js";

/**
 * Event Bus Configuration
 */
const eventBusConfig: EventBusConfig = {
  // Batching configuration
  batchSize: Number(process.env.OBSERVER_BATCH_SIZE) || 50, // Flush after 50 events
  batchWaitMs: Number(process.env.OBSERVER_BATCH_WAIT_MS) || 100, // Or after 100ms

  // Redis configuration
  streamPrefix: "observer", // Redis key prefix (observer:events:all, etc.)
  streamMaxLen: 10000, // Keep last 10K events per stream (with trimming)
  eventTtl: 3600, // Event TTL in seconds (1 hour)

  // Feature flag
  enabled: process.env.OBSERVER_ENABLED !== "false", // Disabled if explicitly set to 'false'
};

/**
 * Circuit Breaker Configuration
 */
const circuitBreakerConfig: CircuitBreakerConfig = {
  failureThreshold: 5, // Open circuit after 5 failures
  resetTimeout: 30000, // Wait 30 seconds before attempting recovery
  windowSize: 60000, // Count failures in 60-second sliding window
  successThreshold: 3, // Close circuit after 3 successful operations in half-open state
};

/**
 * Redis Key Patterns
 */
export const OBSERVER_REDIS_KEYS = {
  // Event storage
  event: (eventId: string) => `observer:event:${eventId}`,
  eventsStream: (eventType: string) => `observer:events:${eventType}`,
  eventsGlobal: () => "observer:events:all",

  // Graph nodes
  userNode: (userId: string) => `graph:node:user:${userId}`,
  circleNode: (circleId: string) => `graph:node:circle:${circleId}`,

  // Graph edges
  proximityEdge: (userId: string) => `graph:edge:proximity:${userId}`,
  collisionEdge: (circle1Id: string, circle2Id: string) =>
    `graph:edge:collision:${[circle1Id, circle2Id].sort().join(":")}`,
  missionEdge: (missionId: string) => `graph:edge:mission:${missionId}`,
  matchEdge: (matchId: string) => `graph:edge:match:${matchId}`,
  chatEdge: (matchId: string) => `graph:edge:chat:${matchId}`,
  conversationEdge: (missionId: string) =>
    `graph:edge:conversation:${missionId}`,

  // Indexes
  userEdgesIndex: (userId: string) => `graph:index:user:${userId}:edges`,
  circleEdgesIndex: (circleId: string) =>
    `graph:index:circle:${circleId}:edges`,
  activeEdgesIndex: () => "graph:index:edges:active",

  // Conversation tracking
  conversationMission: (missionId: string) =>
    `conversation:mission:${missionId}`,
  conversationTurns: (missionId: string) => `conversation:turns:${missionId}`,
  conversationState: (missionId: string) => `conversation:state:${missionId}`,
  conversationThinking: (missionId: string, speaker: "owner" | "visitor") =>
    `conversation:thinking:${missionId}:${speaker}`,
  conversationsByUser: (userId: string) => `conversation:index:user:${userId}`,
  conversationsActive: () => "conversation:index:active",
} as const;

/**
 * Event Type Categories
 */
export const EVENT_CATEGORIES = {
  location: ["location.updated", "location.batch_updated"] as const,
  collision: [
    "collision.detected",
    "collision.stability_reached",
    "collision.expired",
  ] as const,
  agentMatch: [
    "agent_match.mission_created",
    "agent_match.mission_started",
    "agent_match.mission_completed",
    "agent_match.mission_failed",
    "agent_match.cooldown_started",
    "agent_match.interview_started",
    "agent_match.interview_completed",
  ] as const,
  match: [
    "match.created",
    "match.accepted",
    "match.rejected",
    "match.expired",
    "match.chat_started",
  ] as const,
  conversation: [
    "conversation.started",
    "conversation.turn_started",
    "conversation.turn_completed",
    "conversation.thinking_started",
    "conversation.thinking_completed",
    "conversation.judge_decision",
    "conversation.completed",
  ] as const,
} as const;

/**
 * Performance Budgets
 */
export const OBSERVER_PERFORMANCE = {
  maxLatencyMs: 5, // Target: <5ms for event emission
  maxBatchFlushMs: 50, // Target: <50ms for batch flush to Redis
  maxMemoryMb: 100, // Target: <100MB for observer system
} as const;

/**
 * Conversation Tracking Configuration
 */
export const CONVERSATION_CONFIG = {
  maxTurns: 6, // Maximum turns per conversation
  thinkingTtl: 30, // TTL for thinking indicator (seconds)
  conversationTtl: 3600, // TTL for conversation data (1 hour)
  maxConversationsPerUser: 10, // Maximum concurrent conversations per user
} as const;

/**
 * Combined Observer Configuration
 */
export const OBSERVER_CONFIG = {
  eventBus: eventBusConfig,
  circuitBreaker: circuitBreakerConfig,
  redisKeys: OBSERVER_REDIS_KEYS,
  eventCategories: EVENT_CATEGORIES,
  performance: OBSERVER_PERFORMANCE,
  conversation: CONVERSATION_CONFIG,
} as const;
