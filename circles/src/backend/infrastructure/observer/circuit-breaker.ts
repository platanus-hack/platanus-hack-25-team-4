/**
 * Circuit Breaker Pattern Implementation
 *
 * Provides fault tolerance for the observer system by preventing cascading failures.
 * When Redis or event processing fails, the circuit opens and events are dropped
 * silently without impacting application performance.
 */

import type { CircuitBreakerConfig, CircuitState } from "./types.js";

/**
 * Circuit breaker for protecting the observer system from cascading failures
 */
export class CircuitBreaker {
  private _state: CircuitState = "closed";
  private failureCount = 0;
  private successCount = 0;
  private lastFailureTime = 0;
  private readonly failures: number[] = [];

  constructor(private readonly config: CircuitBreakerConfig) {}

  /**
   * Get current circuit state
   */
  get state(): CircuitState {
    return this._state;
  }

  /**
   * Record a successful operation
   */
  recordSuccess(): void {
    this.failureCount = 0;
    this.failures.length = 0;

    if (this._state === "half_open") {
      this.successCount++;
      if (this.successCount >= this.config.successThreshold) {
        this._state = "closed";
        this.successCount = 0;
        console.log(
          "[CircuitBreaker] Circuit closed after successful recovery",
        );
      }
    }
  }

  /**
   * Record a failed operation
   */
  recordFailure(): void {
    const now = Date.now();
    this.lastFailureTime = now;

    // Add failure to sliding window
    this.failures.push(now);

    // Remove failures outside the window
    const windowStart = now - this.config.windowSize;
    while (this.failures.length > 0 && this.failures[0]! < windowStart) {
      this.failures.shift();
    }

    // Count failures in window
    this.failureCount = this.failures.length;

    if (this._state === "half_open") {
      // Any failure in half-open state immediately reopens the circuit
      this._state = "open";
      this.successCount = 0;
      console.warn(
        "[CircuitBreaker] Circuit reopened after failure in half-open state",
      );
    } else if (
      this._state === "closed" &&
      this.failureCount >= this.config.failureThreshold
    ) {
      // Too many failures in window - open the circuit
      this._state = "open";
      console.error("[CircuitBreaker] Circuit opened due to failures", {
        failureCount: this.failureCount,
        threshold: this.config.failureThreshold,
      });
    }
  }

  /**
   * Check if circuit should allow operation
   */
  canExecute(): boolean {
    if (this._state === "closed") {
      return true;
    }

    if (this._state === "open") {
      const timeSinceLastFailure = Date.now() - this.lastFailureTime;
      if (timeSinceLastFailure >= this.config.resetTimeout) {
        // Attempt recovery - move to half-open state
        this._state = "half_open";
        this.successCount = 0;
        console.log(
          "[CircuitBreaker] Circuit moved to half-open state, attempting recovery",
        );
        return true;
      }
      return false;
    }

    // half_open state - allow execution to test recovery
    return true;
  }

  /**
   * Execute an operation with circuit breaker protection
   */
  async execute<T>(operation: () => Promise<T>): Promise<T | null> {
    if (!this.canExecute()) {
      return null;
    }

    try {
      const result = await operation();
      this.recordSuccess();
      return result;
    } catch (error) {
      this.recordFailure();
      console.error("[CircuitBreaker] Operation failed", { error });
      return null;
    }
  }

  /**
   * Get circuit breaker statistics
   */
  getStats(): {
    state: CircuitState;
    failureCount: number;
    successCount: number;
    lastFailureTime: number;
  } {
    return {
      state: this._state,
      failureCount: this.failureCount,
      successCount: this.successCount,
      lastFailureTime: this.lastFailureTime,
    };
  }

  /**
   * Reset circuit breaker to initial state
   */
  reset(): void {
    this._state = "closed";
    this.failureCount = 0;
    this.successCount = 0;
    this.lastFailureTime = 0;
    this.failures.length = 0;
    console.log("[CircuitBreaker] Circuit breaker reset");
  }
}
