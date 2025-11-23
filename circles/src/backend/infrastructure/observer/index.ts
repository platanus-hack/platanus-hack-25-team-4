/**
 * Observer Pattern Infrastructure - Public API
 *
 * This module provides the complete observer system for graph visualization.
 * Import from this file to use the observer pattern in your services.
 *
 * Example usage:
 * ```typescript
 * import { Observe, getEventBus, initializeObserver } from '../infrastructure/observer/index.js';
 *
 * // Initialize observer system (in server.ts or app.ts)
 * initializeObserver();
 *
 * // Use decorator in services
 * class MyService {
 *   @Observe({
 *     eventType: 'location.updated',
 *     extractUserId: (args) => args[0] as string,
 *   })
 *   async updateLocation(userId: string, lat: number, lon: number) {
 *     // Business logic
 *   }
 * }
 * ```
 */

import { CircuitBreaker } from "./circuit-breaker.js";
import { getEventBus, resetEventBus, EventBus } from "./event-bus.js";
import { Observe, observe } from "./observable.js";
import { OBSERVER_CONFIG } from "../../config/observer.config.js";

export { Observe, observe, getEventBus, resetEventBus, CircuitBreaker };

export type {
  ObserverEvent,
  EventType,
  NodeType,
  EdgeType,
  GraphNode,
  GraphEdge,
  CircuitState,
  CircuitBreakerConfig,
  EventBusConfig,
  ObserveOptions,
  LocationEventMetadata,
  CollisionEventMetadata,
  MissionEventMetadata,
  MatchEventMetadata,
  ConversationEventMetadata,
  ConversationTurn,
  ConversationState,
  JudgeDecision,
} from "./types.js";

/**
 * Initialize the observer system with configuration
 * Call this once during application startup
 */
export function initializeObserver(): EventBus {
  return getEventBus(OBSERVER_CONFIG.eventBus, OBSERVER_CONFIG.circuitBreaker);
}

/**
 * Check if observer system is enabled
 */
export function isObserverEnabled(): boolean {
  return OBSERVER_CONFIG.eventBus.enabled;
}
