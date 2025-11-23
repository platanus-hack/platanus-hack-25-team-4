/**
 * Event Bus with Batching and Redis Integration
 *
 * Core component of the observer system. Collects events from decorated service methods,
 * batches them for performance, and writes to Redis Streams asynchronously.
 *
 * Features:
 * - Batching: Collects up to N events or waits M milliseconds before flushing
 * - Circuit Breaker: Fails silently when Redis is unavailable
 * - Non-blocking: Fire-and-forget pattern with background flushing
 * - Zero business logic impact: Errors are logged but never thrown
 */

import { ulid } from "ulid";

import { getRedisClient } from "../redis.js";
import { CircuitBreaker } from "./circuit-breaker.js";
import type {
  ObserverEvent,
  EventBusConfig,
  CircuitBreakerConfig,
} from "./types.js";

/**
 * Event Bus singleton for collecting and flushing observer events
 */
export class EventBus {
  private static readonly MAX_BUFFER_SIZE = 10000;
  private buffer: Array<Omit<ObserverEvent, "id" | "timestamp">> = [];
  private flushTimer: NodeJS.Timeout | null = null;
  private circuitBreaker: CircuitBreaker;
  private isShuttingDown = false;

  constructor(
    private readonly config: EventBusConfig,
    circuitBreakerConfig: CircuitBreakerConfig,
  ) {
    this.circuitBreaker = new CircuitBreaker(circuitBreakerConfig);

    // Setup graceful shutdown
    process.on("SIGTERM", () => {
      void this.shutdown();
    });
    process.on("SIGINT", () => {
      void this.shutdown();
    });
  }

  /**
   * Emit an event to the bus (non-blocking, fail-silent)
   */
  emit(event: Omit<ObserverEvent, "id" | "timestamp">): void {
    // Fail-silent if observer disabled
    if (!this.config.enabled) {
      return;
    }

    // Fail-silent if shutting down
    if (this.isShuttingDown) {
      return;
    }

    // Fail-silent if circuit is open
    if (!this.circuitBreaker.canExecute()) {
      return;
    }

    try {
      // Buffer overflow protection
      if (this.buffer.length >= EventBus.MAX_BUFFER_SIZE) {
        console.warn("[EventBus] Buffer overflow, dropping oldest events", {
          bufferSize: this.buffer.length,
          droppedCount: Math.floor(EventBus.MAX_BUFFER_SIZE / 2),
        });
        // Drop oldest half of buffer to make room
        this.buffer = this.buffer.slice(-Math.floor(EventBus.MAX_BUFFER_SIZE / 2));
      }

      // Add to buffer
      this.buffer.push(event);

      // Schedule flush if not already scheduled
      if (!this.flushTimer) {
        this.scheduleFlush();
      }

      // Immediate flush if batch is full
      if (this.buffer.length >= this.config.batchSize) {
        this.flush();
      }
    } catch (error) {
      // Fail-silent - log but don't throw
      console.error("[EventBus] Failed to emit event", {
        error,
        eventType: event.type,
      });
    }
  }

  /**
   * Schedule a flush after batchWaitMs
   */
  private scheduleFlush(): void {
    this.flushTimer = setTimeout(() => {
      this.flush();
    }, this.config.batchWaitMs);
  }

  /**
   * Flush buffered events to Redis (async, non-blocking)
   */
  private flush(): void {
    // Clear timer
    if (this.flushTimer) {
      clearTimeout(this.flushTimer);
      this.flushTimer = null;
    }

    // Nothing to flush
    if (this.buffer.length === 0) {
      return;
    }

    // Take events from buffer (swap and clear)
    const eventsToFlush = this.buffer;
    this.buffer = [];

    // Fire-and-forget async flush
    this.flushToRedis(eventsToFlush).catch((error) => {
      console.error("[EventBus] Flush failed", {
        error,
        eventCount: eventsToFlush.length,
      });
    });
  }

  /**
   * Flush events to Redis using pipelined operations
   */
  private async flushToRedis(
    events: Array<Omit<ObserverEvent, "id" | "timestamp">>,
  ): Promise<void> {
    if (events.length === 0) {
      return;
    }

    const result = await this.circuitBreaker.execute(async () => {
      const redis = getRedisClient();
      const pipeline = redis.pipeline();
      const now = Date.now();

      for (const event of events) {
        // Add unique ID and timestamp
        const fullEvent: ObserverEvent = {
          ...event,
          id: ulid(),
          timestamp: now,
        };

        const eventKey = `${this.config.streamPrefix}:event:${fullEvent.id}`;
        const streamKey = `${this.config.streamPrefix}:events:${fullEvent.type}`;
        const globalStreamKey = `${this.config.streamPrefix}:events:all`;

        // Store event hash
        pipeline.hset(eventKey, {
          id: fullEvent.id,
          type: fullEvent.type,
          timestamp: fullEvent.timestamp.toString(),
          userId: fullEvent.userId,
          relatedUserId: fullEvent.relatedUserId || "",
          circleId: fullEvent.circleId || "",
          metadata: JSON.stringify(fullEvent.metadata),
        });

        // Set TTL
        pipeline.expire(eventKey, this.config.eventTtl);

        // Add to type-specific stream
        pipeline.xadd(
          streamKey,
          "MAXLEN",
          "~",
          this.config.streamMaxLen,
          "*",
          "eventId",
          fullEvent.id,
          "timestamp",
          fullEvent.timestamp.toString(),
        );

        // Add to global stream
        pipeline.xadd(
          globalStreamKey,
          "MAXLEN",
          "~",
          this.config.streamMaxLen,
          "*",
          "eventId",
          fullEvent.id,
          "type",
          fullEvent.type,
          "timestamp",
          fullEvent.timestamp.toString(),
        );
      }

      // Execute pipeline
      await pipeline.exec();

      return true;
    });

    if (result === null) {
      // Circuit breaker prevented execution or operation failed
      console.warn("[EventBus] Events dropped due to circuit breaker", {
        eventCount: events.length,
        circuitState: this.circuitBreaker.state,
      });
    }
  }

  /**
   * Graceful shutdown - flush remaining events
   */
  private async shutdown(): Promise<void> {
    if (this.isShuttingDown) {
      return;
    }

    this.isShuttingDown = true;
    console.log("[EventBus] Shutting down, flushing remaining events...");

    // Clear timer
    if (this.flushTimer) {
      clearTimeout(this.flushTimer);
      this.flushTimer = null;
    }

    // Flush remaining events
    if (this.buffer.length > 0) {
      try {
        await this.flushToRedis(this.buffer);
        console.log("[EventBus] Shutdown complete, events flushed");
      } catch (error) {
        console.error("[EventBus] Failed to flush events during shutdown", {
          error,
        });
      }
    }

    this.buffer = [];
  }

  /**
   * Get current buffer size
   */
  getBufferSize(): number {
    return this.buffer.length;
  }

  /**
   * Get circuit breaker stats
   */
  getCircuitStats() {
    return this.circuitBreaker.getStats();
  }

  /**
   * Manually trigger flush (useful for testing)
   */
  async forceFlush(): Promise<void> {
    if (this.buffer.length === 0) {
      return;
    }

    const events = this.buffer;
    this.buffer = [];

    if (this.flushTimer) {
      clearTimeout(this.flushTimer);
      this.flushTimer = null;
    }

    await this.flushToRedis(events);
  }
}

/**
 * Singleton instance (lazy initialization)
 */
let eventBusInstance: EventBus | null = null;

/**
 * Get or create the EventBus singleton
 */
export function getEventBus(
  config?: EventBusConfig,
  circuitBreakerConfig?: CircuitBreakerConfig,
): EventBus {
  if (!eventBusInstance) {
    if (!config || !circuitBreakerConfig) {
      throw new Error(
        "EventBus not initialized. Call getEventBus with config on first use.",
      );
    }
    eventBusInstance = new EventBus(config, circuitBreakerConfig);
  }
  return eventBusInstance;
}

/**
 * Reset the EventBus instance (useful for testing)
 */
export function resetEventBus(): void {
  eventBusInstance = null;
}
