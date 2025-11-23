/**
 * @Observe Decorator for Service Methods
 *
 * Provides a non-invasive way to add observer pattern to existing service methods.
 * The decorator wraps methods and emits events to the EventBus without modifying
 * the original business logic.
 *
 * Usage:
 * ```typescript
 * @Observe({
 *   eventType: 'location.updated',
 *   extractUserId: (args) => args[0] as string,
 *   buildMetadata: (args, result) => ({
 *     latitude: args[1],
 *     longitude: args[2],
 *   }),
 * })
 * async updateUserLocation(userId: string, lat: number, lon: number) {
 *   // Original business logic unchanged
 * }
 * ```
 */

import { getEventBus } from "./event-bus.js";
import type { ObserveOptions } from "./types.js";

/**
 * Method decorator that emits observer events
 */
export function Observe(options: ObserveOptions): MethodDecorator {
  return function (
    _target: unknown,
    _propertyKey: string | symbol,
    descriptor: PropertyDescriptor,
  ): PropertyDescriptor {
    const originalMethod = descriptor.value;

    if (typeof originalMethod !== "function") {
      throw new Error(
        `@Observe can only be applied to methods, not ${typeof originalMethod}`,
      );
    }

    // Wrap the original method
    descriptor.value = async function (this: unknown, ...args: unknown[]) {
      let result: unknown;
      let error: unknown;

      try {
        // Execute original method
        result = await originalMethod.apply(this, args);
      } catch (err) {
        error = err;

        // Only emit event on error if configured to do so
        if (options.emitOnError) {
          emitEvent(options, args, String(err));
        }

        // Re-throw to maintain original error handling
        throw err;
      }

      // Emit event on success
      if (!error) {
        emitEvent(options, args, result);
      }

      return result;
    };

    return descriptor;
  };
}

/**
 * Helper function to emit event from decorator
 */
function emitEvent(
  options: ObserveOptions,
  args: unknown[],
  result: unknown,
): void {
  try {
    // Extract required fields
    const userId = options.extractUserId(args);
    if (!userId || typeof userId !== "string") {
      console.warn(
        "[Observe] Failed to extract userId, skipping event emission",
        {
          eventType: options.eventType,
        },
      );
      return;
    }

    // Extract optional fields
    const relatedUserId = options.extractRelatedUserId?.(args);
    const circleId = options.extractCircleId?.(args);

    // Build metadata
    const metadata = options.buildMetadata
      ? options.buildMetadata(args, result)
      : { result };

    // Get event bus and emit
    const eventBus = getEventBus();
    eventBus.emit({
      type: options.eventType,
      userId,
      relatedUserId,
      circleId,
      metadata,
    });
  } catch (error) {
    // Fail-silent - decorator errors should never impact business logic
    console.error("[Observe] Failed to emit event", {
      error,
      eventType: options.eventType,
    });
  }
}

/**
 * Alternative functional API for cases where decorators can't be used
 */
export function observe(
  options: ObserveOptions,
  fn: (...args: unknown[]) => Promise<unknown>,
): (...args: unknown[]) => Promise<unknown> {
  return async function (this: unknown, ...args: unknown[]) {
    let result: unknown;
    let error: unknown;

    try {
      result = await fn.apply(this, args);
    } catch (err) {
      error = err;

      if (options.emitOnError) {
        emitEvent(options, args, String(err));
      }

      throw err;
    }

    if (!error) {
      emitEvent(options, args, result);
    }

    return result;
  };
}
