import { Redis } from 'ioredis';

let redisClient: Redis | null = null;

export const getRedisClient = (): Redis => {
  if (redisClient) {
    return redisClient;
  }

  const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';

  const client = new Redis(redisUrl, {
    // For collision state, NOT for blocking (that's handled by BullMQ)
    maxRetriesPerRequest: null,
    retryStrategy: (times: number) => {
      const delay = Math.min(times * 50, 2000);
      return delay;
    },
    enableReadyCheck: true,
    enableOfflineQueue: false,
    connectTimeout: 10000,
  });

  client.on('connect', () => {
    console.log('Redis client connected');
  });

  client.on('error', (error: Error) => {
    console.error('Redis client error:', error.message);
  });

  client.on('close', () => {
    console.warn('Redis client connection closed');
  });

  client.on('reconnecting', () => {
    console.info('Redis client reconnecting');
  });

  redisClient = client;
  return redisClient;
};

export const closeRedis = async (): Promise<void> => {
  if (redisClient) {
    await redisClient.quit();
    redisClient = null;
  }
};

// Health check
export const checkRedisHealth = async (): Promise<boolean> => {
  try {
    const client = getRedisClient();
    const result = await client.ping();
    return result === 'PONG';
  } catch (error) {
    console.error('Redis health check failed:', error);
    return false;
  }
};
