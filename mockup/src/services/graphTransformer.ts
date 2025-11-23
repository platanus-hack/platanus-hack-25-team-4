import type {
  ObserverEvent,
  GraphNode,
  GraphEdge,
  GraphData,
  EventCategory,
  CollisionEventMetadata,
  MissionEventMetadata,
  MatchEventMetadata,
} from '../types/observer.types';

/**
 * Transform observer events into D3-compatible graph nodes and edges
 */
class GraphTransformer {
  /**
   * Convert array of observer events into graph data structure
   */
  transform(events: ObserverEvent[]): GraphData {
    const nodesMap = new Map<string, GraphNode>();
    const edgesMap = new Map<string, GraphEdge>();

    for (const event of events) {
      this.processEvent(event, nodesMap, edgesMap);
    }

    return {
      nodes: Array.from(nodesMap.values()),
      edges: Array.from(edgesMap.values()),
    };
  }

  /**
   * Process a single event and update nodes/edges maps
   */
  private processEvent(
    event: ObserverEvent,
    nodesMap: Map<string, GraphNode>,
    edgesMap: Map<string, GraphEdge>
  ): void {
    const category = this.getEventCategory(event.eventType);

    // Always create/update node for the primary user
    this.addOrUpdateNode(
      nodesMap,
      event.userId,
      `User ${event.userId.slice(0, 8)}`,
      'user',
      category,
      event.timestamp,
      event.metadata
    );

    // Process based on event category
    switch (category) {
      case 'location':
        this.processLocationEvent(event, nodesMap);
        break;
      case 'collision':
        this.processCollisionEvent(event, nodesMap, edgesMap);
        break;
      case 'mission':
      case 'agent_match':
        this.processMissionEvent(event, nodesMap, edgesMap);
        break;
      case 'match':
      case 'chat':
        this.processMatchEvent(event, nodesMap, edgesMap);
        break;
      case 'conversation':
        this.processConversationEvent(event, nodesMap, edgesMap);
        break;
    }
  }

  private processLocationEvent(
    event: ObserverEvent,
    nodesMap: Map<string, GraphNode>
  ): void {
    // Location events just update the user node
    // No edges created for location alone
    const node = nodesMap.get(event.userId);
    if (node && event.metadata) {
      node.metadata = { ...node.metadata, ...event.metadata };
    }
  }

  private processCollisionEvent(
    event: ObserverEvent,
    nodesMap: Map<string, GraphNode>,
    edgesMap: Map<string, GraphEdge>
  ): void {
    const metadata = event.metadata as unknown as CollisionEventMetadata;
    if (!metadata.user2Id) return;

    // Create node for other user
    this.addOrUpdateNode(
      nodesMap,
      metadata.user2Id,
      `User ${metadata.user2Id.slice(0, 8)}`,
      'user',
      'collision',
      event.timestamp,
      {}
    );

    // Create edge between users
    const edgeId = `collision:${event.userId}:${metadata.user2Id}`;
    this.addOrUpdateEdge(
      edgesMap,
      edgeId,
      event.userId,
      metadata.user2Id,
      'collision',
      metadata.distance ? 1 / Math.max(metadata.distance, 1) : 1,
      event.timestamp
    );
  }

  private processMissionEvent(
    event: ObserverEvent,
    nodesMap: Map<string, GraphNode>,
    edgesMap: Map<string, GraphEdge>
  ): void {
    const metadata = event.metadata as unknown as MissionEventMetadata;
    if (!metadata.missionId) return;

    // Create mission node
    this.addOrUpdateNode(
      nodesMap,
      metadata.missionId,
      `Mission ${metadata.missionId.slice(0, 8)}`,
      'mission',
      'mission',
      event.timestamp,
      event.metadata
    );

    // Create edges from users to mission
    if (metadata.ownerUserId) {
      this.addOrUpdateNode(
        nodesMap,
        metadata.ownerUserId,
        `User ${metadata.ownerUserId.slice(0, 8)}`,
        'user',
        'mission',
        event.timestamp,
        {}
      );

      this.addOrUpdateEdge(
        edgesMap,
        `mission:${metadata.ownerUserId}:${metadata.missionId}`,
        metadata.ownerUserId,
        metadata.missionId,
        'mission',
        0.8,
        event.timestamp
      );
    }

    if (metadata.visitorUserId) {
      this.addOrUpdateNode(
        nodesMap,
        metadata.visitorUserId,
        `User ${metadata.visitorUserId.slice(0, 8)}`,
        'user',
        'mission',
        event.timestamp,
        {}
      );

      this.addOrUpdateEdge(
        edgesMap,
        `mission:${metadata.visitorUserId}:${metadata.missionId}`,
        metadata.visitorUserId,
        metadata.missionId,
        'mission',
        0.8,
        event.timestamp
      );
    }
  }

  private processMatchEvent(
    event: ObserverEvent,
    nodesMap: Map<string, GraphNode>,
    edgesMap: Map<string, GraphEdge>
  ): void {
    const metadata = event.metadata as unknown as MatchEventMetadata;
    if (!metadata.user1Id || !metadata.user2Id) return;

    // Create nodes for both users
    this.addOrUpdateNode(
      nodesMap,
      metadata.user1Id,
      `User ${metadata.user1Id.slice(0, 8)}`,
      'user',
      'match',
      event.timestamp,
      {}
    );

    this.addOrUpdateNode(
      nodesMap,
      metadata.user2Id,
      `User ${metadata.user2Id.slice(0, 8)}`,
      'user',
      'match',
      event.timestamp,
      {}
    );

    // Create edge between matched users
    this.addOrUpdateEdge(
      edgesMap,
      `match:${metadata.matchId}`,
      metadata.user1Id,
      metadata.user2Id,
      'match',
      0.9,
      event.timestamp
    );
  }

  private processConversationEvent(
    event: ObserverEvent,
    nodesMap: Map<string, GraphNode>,
    edgesMap: Map<string, GraphEdge>
  ): void {
    const metadata = event.metadata as { missionId?: string };
    if (!metadata.missionId) return;

    // Create/update conversation node
    this.addOrUpdateNode(
      nodesMap,
      metadata.missionId,
      `Conv ${metadata.missionId.slice(0, 8)}`,
      'conversation',
      'conversation',
      event.timestamp,
      event.metadata
    );

    // Create edge from user to conversation
    this.addOrUpdateEdge(
      edgesMap,
      `conv:${event.userId}:${metadata.missionId}`,
      event.userId,
      metadata.missionId,
      'conversation',
      0.7,
      event.timestamp
    );
  }

  private addOrUpdateNode(
    nodesMap: Map<string, GraphNode>,
    id: string,
    label: string,
    type: GraphNode['type'],
    category: EventCategory,
    timestamp: number,
    metadata: Record<string, unknown>
  ): void {
    const existing = nodesMap.get(id);

    if (existing) {
      // Update existing node
      existing.eventCount += 1;
      existing.lastActive = Math.max(existing.lastActive, timestamp);
      existing.metadata = { ...existing.metadata, ...metadata };
    } else {
      // Create new node
      nodesMap.set(id, {
        id,
        label,
        type,
        category,
        eventCount: 1,
        lastActive: timestamp,
        metadata,
      });
    }
  }

  private addOrUpdateEdge(
    edgesMap: Map<string, GraphEdge>,
    id: string,
    source: string,
    target: string,
    type: EventCategory,
    strength: number,
    timestamp: number
  ): void {
    const existing = edgesMap.get(id);

    if (existing) {
      // Update existing edge
      existing.eventCount += 1;
      existing.lastActive = Math.max(existing.lastActive, timestamp);
      existing.strength = Math.min(existing.strength + 0.1, 1);
    } else {
      // Create new edge
      edgesMap.set(id, {
        id,
        source,
        target,
        type,
        strength,
        eventCount: 1,
        lastActive: timestamp,
      });
    }
  }

  private getEventCategory(eventType: string): EventCategory {
    if (eventType.startsWith('location.')) return 'location';
    if (eventType.startsWith('collision.')) return 'collision';
    if (eventType.startsWith('mission.')) return 'mission';
    if (eventType.startsWith('agent_match.')) return 'agent_match';
    if (eventType.startsWith('match.')) return 'match';
    if (eventType.startsWith('conversation.')) return 'conversation';
    if (eventType.startsWith('chat.')) return 'chat';
    return 'all';
  }

  /**
   * Get color for a category
   */
  getCategoryColor(category: EventCategory): string {
    const colorMap: Record<EventCategory, string> = {
      location: '#3B82F6', // Blue
      collision: '#EF4444', // Red
      mission: '#A855F7', // Purple
      agent_match: '#A855F7', // Purple
      match: '#EC4899', // Pink
      conversation: '#10B981', // Green
      chat: '#06B6D4', // Cyan
      all: '#6B7280', // Gray
    };

    return colorMap[category] || '#6B7280';
  }

  /**
   * Get node radius based on event count
   */
  getNodeRadius(eventCount: number): number {
    return Math.min(5 + eventCount * 2, 20);
  }
}

export const graphTransformer = new GraphTransformer();
export { GraphTransformer };
