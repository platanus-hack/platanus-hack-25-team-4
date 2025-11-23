import { describe, it, expect, beforeEach } from "vitest";

import { CircuitBreaker } from "../../infrastructure/observer/circuit-breaker.js";
import type { CircuitBreakerConfig } from "../../infrastructure/observer/types.js";

describe("CircuitBreaker", () => {
  let circuitBreaker: CircuitBreaker;
  let config: CircuitBreakerConfig;

  beforeEach(() => {
    config = {
      failureThreshold: 3,
      resetTimeout: 1000,
      windowSize: 5000,
      successThreshold: 2,
    };
    circuitBreaker = new CircuitBreaker(config);
  });

  describe("initial state", () => {
    it("should start in closed state", () => {
      expect(circuitBreaker.state).toBe("closed");
      expect(circuitBreaker.canExecute()).toBe(true);
    });

    it("should have zero failure count", () => {
      const stats = circuitBreaker.getStats();
      expect(stats.failureCount).toBe(0);
      expect(stats.successCount).toBe(0);
    });
  });

  describe("failure handling", () => {
    it("should allow execution when failures are below threshold", () => {
      circuitBreaker.recordFailure();
      circuitBreaker.recordFailure();

      expect(circuitBreaker.state).toBe("closed");
      expect(circuitBreaker.canExecute()).toBe(true);
    });

    it("should open circuit when failures reach threshold", () => {
      circuitBreaker.recordFailure();
      circuitBreaker.recordFailure();
      circuitBreaker.recordFailure();

      expect(circuitBreaker.state).toBe("open");
      expect(circuitBreaker.canExecute()).toBe(false);
    });

    it("should count failures in sliding window", async () => {
      // Create circuit breaker with short window
      const shortWindowConfig: CircuitBreakerConfig = {
        ...config,
        windowSize: 100, // 100ms window
      };
      const cb = new CircuitBreaker(shortWindowConfig);

      // Record 2 failures
      cb.recordFailure();
      cb.recordFailure();

      // Wait for window to expire
      await new Promise((resolve) => setTimeout(resolve, 150));

      // Record 1 more failure - should not open circuit
      cb.recordFailure();

      expect(cb.state).toBe("closed");
    });

    it("should track multiple failures correctly", () => {
      circuitBreaker.recordFailure();
      circuitBreaker.recordFailure();

      const stats = circuitBreaker.getStats();
      expect(stats.failureCount).toBe(2);
    });
  });

  describe("success handling", () => {
    it("should reset failure count on success", () => {
      circuitBreaker.recordFailure();
      circuitBreaker.recordFailure();
      circuitBreaker.recordSuccess();

      const stats = circuitBreaker.getStats();
      expect(stats.failureCount).toBe(0);
    });

    it("should close circuit from half-open after success threshold", async () => {
      // Open the circuit
      circuitBreaker.recordFailure();
      circuitBreaker.recordFailure();
      circuitBreaker.recordFailure();
      expect(circuitBreaker.state).toBe("open");

      // Wait for reset timeout
      await new Promise((resolve) => setTimeout(resolve, 1100));

      // Move to half-open
      expect(circuitBreaker.canExecute()).toBe(true);
      expect(circuitBreaker.state).toBe("half_open");

      // Record successes
      circuitBreaker.recordSuccess();
      expect(circuitBreaker.state).toBe("half_open");

      circuitBreaker.recordSuccess();
      expect(circuitBreaker.state).toBe("closed");
    });
  });

  describe("state transitions", () => {
    it("should transition: closed -> open -> half_open -> closed", async () => {
      // Start closed
      expect(circuitBreaker.state).toBe("closed");

      // Transition to open
      circuitBreaker.recordFailure();
      circuitBreaker.recordFailure();
      circuitBreaker.recordFailure();
      expect(circuitBreaker.state).toBe("open");

      // Wait for reset timeout
      await new Promise((resolve) => setTimeout(resolve, 1100));

      // Transition to half_open
      expect(circuitBreaker.canExecute()).toBe(true);
      expect(circuitBreaker.state).toBe("half_open");

      // Transition back to closed
      circuitBreaker.recordSuccess();
      circuitBreaker.recordSuccess();
      expect(circuitBreaker.state).toBe("closed");
    });

    it("should reopen from half-open on failure", async () => {
      // Open the circuit
      circuitBreaker.recordFailure();
      circuitBreaker.recordFailure();
      circuitBreaker.recordFailure();
      expect(circuitBreaker.state).toBe("open");

      // Wait for reset timeout
      await new Promise((resolve) => setTimeout(resolve, 1100));

      // Move to half-open
      circuitBreaker.canExecute();
      expect(circuitBreaker.state).toBe("half_open");

      // Failure reopens circuit
      circuitBreaker.recordFailure();
      expect(circuitBreaker.state).toBe("open");
    });
  });

  describe("execute method", () => {
    it("should execute operation when circuit is closed", async () => {
      const operation = async () => "success";
      const result = await circuitBreaker.execute(operation);

      expect(result).toBe("success");
    });

    it("should return null when circuit is open", async () => {
      // Open the circuit
      circuitBreaker.recordFailure();
      circuitBreaker.recordFailure();
      circuitBreaker.recordFailure();

      const operation = async () => "success";
      const result = await circuitBreaker.execute(operation);

      expect(result).toBeNull();
    });

    it("should record failure when operation throws", async () => {
      const operation = async () => {
        throw new Error("Operation failed");
      };

      const result = await circuitBreaker.execute(operation);

      expect(result).toBeNull();
      expect(circuitBreaker.getStats().failureCount).toBe(1);
    });

    it("should record success when operation completes", async () => {
      circuitBreaker.recordFailure();
      expect(circuitBreaker.getStats().failureCount).toBe(1);

      const operation = async () => "success";
      await circuitBreaker.execute(operation);

      expect(circuitBreaker.getStats().failureCount).toBe(0);
    });
  });

  describe("reset", () => {
    it("should reset circuit breaker to initial state", () => {
      // Accumulate state
      circuitBreaker.recordFailure();
      circuitBreaker.recordFailure();
      circuitBreaker.recordFailure();
      expect(circuitBreaker.state).toBe("open");

      // Reset
      circuitBreaker.reset();

      // Verify initial state
      expect(circuitBreaker.state).toBe("closed");
      expect(circuitBreaker.getStats().failureCount).toBe(0);
      expect(circuitBreaker.getStats().successCount).toBe(0);
    });
  });
});
