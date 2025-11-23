import { Router, type Request, type Response } from 'express';

import { OBSERVER_REDIS_KEYS } from '../config/observer.config.js';
import { getEventBus } from '../infrastructure/observer/index.js';
import { getRedisClient } from '../infrastructure/redis.js';

const observerRouter = Router();

/**
 * GET /observer/stats
 * Get aggregated counts for users, events, and conversations
 */
observerRouter.get('/stats', (_req: Request, res: Response) => {
  void (async () => {
  try {
    const redis = getRedisClient();
    const eventBus = getEventBus();

    // Get unique user count from active users index
    const activeUsers = await redis.smembers(OBSERVER_REDIS_KEYS.activeUsersIndex());
    const uniqueUserCount = activeUsers.length;

    // Get total event count across all streams
    const allStreamsKey = OBSERVER_REDIS_KEYS.eventsStream('all');
    const streamInfo = await redis.xinfo('STREAM', allStreamsKey).catch(() => null);
    const totalEvents = streamInfo && Array.isArray(streamInfo) && streamInfo.length > 7 ? streamInfo[7] : 0; // Index 7 is length

    // Get active conversation count
    const activeConversations = await redis.smembers(
      OBSERVER_REDIS_KEYS.activeConversationsIndex(),
    );
    const activeConversationCount = activeConversations.length;

    // Get circuit breaker status
    const circuitStats = eventBus.getCircuitStats();
    const bufferSize = eventBus.getBufferSize();

    res.json({
      stats: {
        uniqueUsers: uniqueUserCount,
        totalEvents: Number(totalEvents),
        activeConversations: activeConversationCount,
      },
      observer: {
        bufferSize,
        circuitState: circuitStats.state,
        failureCount: circuitStats.failureCount,
        successCount: circuitStats.successCount,
      },
    });
  } catch (error) {
    console.error('[Observer Stats] Failed to get stats', { error });
    res.status(500).json({
      error: 'Failed to retrieve observer stats',
      stats: {
        uniqueUsers: 0,
        totalEvents: 0,
        activeConversations: 0,
      },
    });
  }
  })();
});

/**
 * GET /observer/events/:type
 * Get recent events of a specific type
 */
observerRouter.get('/events/:type', (req: Request, res: Response) => {
  void (async () => {
  try {
    const { type = 'all' } = req.params;
    const limit = Math.min(Number(req.query.limit) || 100, 1000); // Max 1000 events

    const redis = getRedisClient();
    const streamKey = OBSERVER_REDIS_KEYS.eventsStream(type);

    // Get last N events from stream
    const events = await redis.xrevrange(streamKey, '+', '-', 'COUNT', limit);

    const formattedEvents = events.map((entry) => {
      const [eventId, fields] = entry;
      // fields is an array like ['field1', 'value1', 'field2', 'value2']
      const eventData: Record<string, string> = {};
      for (let i = 0; i < fields.length; i += 2) {
        const field = fields[i];
        const value = fields[i + 1];
        if (typeof field === 'string' && typeof value === 'string') {
          eventData[field] = value;
        }
      }
      return {
        id: eventId,
        ...eventData,
        timestamp: Number(eventData.timestamp),
      };
    });

    res.json({
      eventType: type,
      count: formattedEvents.length,
      events: formattedEvents,
    });
  } catch (error) {
    console.error('[Observer Events] Failed to get events', { error });
    res.status(500).json({
      error: 'Failed to retrieve events',
      events: [],
    });
  }
  })();
});

/**
 * GET /observer/users/:userId/activity
 * Get recent activity for a specific user
 */
observerRouter.get('/users/:userId/activity', (req: Request, res: Response) => {
  void (async () => {
  try {
    const { userId } = req.params;
    const limit = Math.min(Number(req.query.limit) || 50, 500);

    const redis = getRedisClient();

    // Get events across all streams for this user
    // We'll scan the main event stream and filter by userId
    const allStreamsKey = OBSERVER_REDIS_KEYS.eventsStream('all');
    const events = await redis.xrevrange(allStreamsKey, '+', '-', 'COUNT', limit * 2);

    // Filter events by userId
    const userEvents = events
      .map((entry): Record<string, string> & { id: string } => {
        const [eventId, fields] = entry;
        const eventData: Record<string, string> = {};
        for (let i = 0; i < fields.length; i += 2) {
          const field = fields[i];
          const value = fields[i + 1];
          if (typeof field === 'string' && typeof value === 'string') {
            eventData[field] = value;
          }
        }
        return {
          id: eventId,
          ...eventData,
        };
      })
      .filter((event) => {
        const userId = event['userId'];
        const relatedUserId = event['relatedUserId'];
        return userId === req.params.userId || relatedUserId === req.params.userId;
      })
      .slice(0, limit);

    res.json({
      userId,
      activityCount: userEvents.length,
      events: userEvents,
    });
  } catch (error) {
    console.error('[Observer User Activity] Failed to get activity', { error });
    res.status(500).json({
      error: 'Failed to retrieve user activity',
      events: [],
    });
  }
  })();
});

export { observerRouter };
