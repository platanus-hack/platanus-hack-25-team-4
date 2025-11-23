/**
 * Observer Pattern Type Definitions
 *
 * Defines all types for the graph visualization observer system.
 * These events are emitted by services and stored in Redis for graph construction.
 */

/**
 * All possible event types in the system
 */
export type EventType =
  // Location events
  | "location.updated"
  | "location.batch_updated"

  // Collision events
  | "collision.detected"
  | "collision.stability_reached"
  | "collision.expired"

  // Agent Match events
  | "agent_match.mission_created"
  | "agent_match.mission_started"
  | "agent_match.mission_completed"
  | "agent_match.mission_failed"
  | "agent_match.cooldown_started"
  | "agent_match.interview_started"
  | "agent_match.interview_completed"

  // Match events
  | "match.created"
  | "match.accepted"
  | "match.rejected"
  | "match.expired"
  | "match.chat_started"

  // Conversation events
  | "conversation.started"
  | "conversation.turn_started"
  | "conversation.turn_completed"
  | "conversation.thinking_started"
  | "conversation.thinking_completed"
  | "conversation.judge_decision"
  | "conversation.completed";

/**
 * Base observer event structure
 */
export interface ObserverEvent {
  /** Unique event ID (ULID or UUID) */
  id: string;

  /** Event type */
  type: EventType;

  /** Unix timestamp in milliseconds */
  timestamp: number;

  /** Primary user ID (for indexing) */
  userId: string;

  /** Secondary user ID (for two-user events like collisions, matches) */
  relatedUserId?: string;

  /** Circle ID (if applicable) */
  circleId?: string;

  /** Event-specific metadata */
  metadata: Record<string, unknown>;
}

/**
 * Location update event metadata
 */
export interface LocationEventMetadata {
  latitude: number;
  longitude: number;
  accuracy?: number;
  previousLat?: number;
  previousLon?: number;
  distanceMoved?: number;
}

/**
 * Collision event metadata
 */
export interface CollisionEventMetadata {
  circle1Id: string;
  circle2Id: string;
  distance: number;
  collisionRadius: number;
  isStable?: boolean;
  stabilityDuration?: number;
}

/**
 * Mission event metadata
 */
export interface MissionEventMetadata {
  missionId: string;
  ownerUserId: string;
  visitorUserId: string;
  ownerCircleId: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  duration?: number;
  outcome?: "success" | "failure" | "timeout";
}

/**
 * Match event metadata
 */
export interface MatchEventMetadata {
  matchId: string;
  user1Id: string;
  user2Id: string;
  status: "pending" | "accepted" | "rejected" | "expired";
  chatStarted?: boolean;
}

/**
 * Conversation event metadata
 */
export interface ConversationEventMetadata {
  missionId: string;
  speaker?: "owner" | "visitor";
  turnNumber?: number;
  message?: string;
  isThinking?: boolean;
  judgeDecision?: {
    approved: boolean;
    score: number;
    reasoning: string;
  };
}

/**
 * Graph node types
 */
export type NodeType = "user" | "circle";

/**
 * Graph edge types
 */
export type EdgeType =
  | "proximity"
  | "collision"
  | "mission"
  | "match"
  | "chat"
  | "conversation";

/**
 * Graph node structure (stored in Redis)
 */
export interface GraphNode {
  id: string;
  type: NodeType;
  createdAt: number;
  updatedAt: number;
  metadata: Record<string, unknown>;
}

/**
 * Graph edge structure (stored in Redis)
 */
export interface GraphEdge {
  id: string;
  type: EdgeType;
  source: string;
  target: string;
  createdAt: number;
  updatedAt: number;
  weight?: number;
  metadata: Record<string, unknown>;
}

/**
 * Circuit breaker states
 */
export type CircuitState = "closed" | "open" | "half_open";

/**
 * Circuit breaker configuration
 */
export interface CircuitBreakerConfig {
  /** Number of failures before opening circuit */
  failureThreshold: number;

  /** Time in ms to wait before attempting to close circuit */
  resetTimeout: number;

  /** Window size in ms for counting failures */
  windowSize: number;

  /** Number of successful requests needed to close circuit from half-open */
  successThreshold: number;
}

/**
 * Event bus configuration
 */
export interface EventBusConfig {
  /** Maximum events in batch before flushing */
  batchSize: number;

  /** Maximum time in ms to wait before flushing */
  batchWaitMs: number;

  /** Redis key prefix for event streams */
  streamPrefix: string;

  /** Maximum length of event streams (trimming) */
  streamMaxLen: number;

  /** TTL for events in seconds */
  eventTtl: number;

  /** Enable/disable observer system */
  enabled: boolean;
}

/**
 * Decorator options for @Observe
 */
export interface ObserveOptions {
  /** Event type to emit */
  eventType: EventType;

  /** Function to extract userId from method arguments */
  extractUserId: (args: unknown[]) => string;

  /** Optional function to extract relatedUserId from method arguments */
  extractRelatedUserId?: (args: unknown[]) => string | undefined;

  /** Optional function to extract circleId from method arguments */
  extractCircleId?: (args: unknown[]) => string | undefined;

  /** Optional function to build custom metadata from arguments and result */
  buildMetadata?: (args: unknown[], result: unknown) => Record<string, unknown>;

  /** Whether to emit on method error (default: false) */
  emitOnError?: boolean;
}

/**
 * Conversation turn structure
 */
export interface ConversationTurn {
  turnNumber: number;
  speaker: "owner" | "visitor";
  message: string;
  timestamp: number;
  thinkingDuration?: number;
}

/**
 * Conversation state
 */
export interface ConversationState {
  missionId: string;
  ownerUserId: string;
  visitorUserId: string;
  ownerCircleId: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  turnCount: number;
  currentSpeaker?: "owner" | "visitor";
  isThinking: boolean;
  createdAt: number;
  updatedAt: number;
  completedAt?: number;
}

/**
 * Judge decision structure
 */
export interface JudgeDecision {
  approved: boolean;
  score: number;
  reasoning: string;
  timestamp: number;
}
