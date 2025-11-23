// Observer Event Types
export type EventType =
  | 'location.updated'
  | 'location.batch_updated'
  | 'collision.detected'
  | 'collision.stability_reached'
  | 'collision.expired'
  | 'mission.started'
  | 'mission.completed'
  | 'mission.failed'
  | 'agent_match.mission_created'
  | 'match.created'
  | 'match.accepted'
  | 'match.rejected'
  | 'match.expired'
  | 'match.chat_started'
  | 'conversation.started'
  | 'conversation.turn_started'
  | 'conversation.turn_completed'
  | 'conversation.completed';

export type EventCategory =
  | 'location'
  | 'collision'
  | 'mission'
  | 'agent_match'
  | 'match'
  | 'conversation'
  | 'chat'
  | 'all';

// Base Observer Event
export interface ObserverEvent {
  eventId: string;
  eventType: EventType;
  userId: string;
  timestamp: number;
  metadata: Record<string, unknown>;
}

// Specific Event Metadata Types
export interface LocationEventMetadata {
  latitude: number;
  longitude: number;
  accuracy: number;
  timestamp: number;
  skipped?: boolean;
  collisionsDetected?: number;
  distanceMoved?: number;
}

export interface CollisionEventMetadata {
  circle1Id: string | null;
  circle2Id: string;
  user1Id: string;
  user2Id: string;
  distance: number;
  collisionRadius?: number;
  collisionCount?: number;
  collisions?: Array<{
    circleId: string;
    otherUserId: string;
    distance: number;
  }>;
}

export interface MissionEventMetadata {
  missionId: string;
  ownerUserId: string;
  visitorUserId: string;
  status: string;
  duration?: number;
  outcome?: string;
  conversationId?: string;
}

export interface MatchEventMetadata {
  matchId: string;
  user1Id: string;
  user2Id: string;
  status: string;
  chatId?: string;
}

export interface ConversationEventMetadata {
  missionId: string;
  speaker: string;
  turnNumber: number;
  message?: string;
  judgeDecision?: string;
  finalOutcome?: string;
  totalTurns?: number;
}

// API Response Types
export interface ObserverStats {
  stats: {
    uniqueUsers: number;
    totalEvents: number;
    activeConversations: number;
  };
  observer: {
    bufferSize: number;
    circuitState: 'closed' | 'open' | 'half_open';
    failureCount: number;
    successCount: number;
  };
}

export interface EventsResponse {
  events: ObserverEvent[];
  count: number;
  type: EventCategory;
}

export interface UserActivityResponse {
  userId: string;
  events: ObserverEvent[];
  count: number;
}

// Graph Data Types for D3
export interface GraphNode {
  id: string;
  label: string;
  type: 'user' | 'circle' | 'mission' | 'conversation';
  category: EventCategory;
  eventCount: number;
  lastActive: number;
  metadata: Record<string, unknown>;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface GraphEdge {
  id: string;
  source: string | GraphNode;
  target: string | GraphNode;
  type: EventCategory;
  strength: number;
  eventCount: number;
  lastActive: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// Filter State
export interface FilterState {
  eventTypes: Set<EventCategory>;
  timeRange: {
    start: number;
    end: number;
  };
  searchQuery: string;
}

// Node Inspector State
export interface SelectedNode {
  node: GraphNode;
  events: ObserverEvent[];
  connections: GraphEdge[];
}
