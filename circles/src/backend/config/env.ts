import { config as loadEnv } from 'dotenv';
import { z } from 'zod';

loadEnv();

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.string().transform((value) => Number.parseInt(value, 10)).default('3000'),
  JWT_SECRET: z.string().min(1).default('change-me'),
  DATABASE_URL: z.string().optional(),
  REDIS_URL: z.string().default('redis://127.0.0.1:6379'),
  MISSION_QUEUE_NAME: z.string().default('interview-missions'),
  MISSION_WORKER_CONCURRENCY: z
    .string()
    .transform((value) => Number.parseInt(value, 10))
    .default('5')
});

const parsedEnv = envSchema.safeParse(process.env);

if (!parsedEnv.success) {
  // eslint-disable-next-line no-console
  console.error('Invalid environment configuration', parsedEnv.error.flatten().fieldErrors);
  throw new Error('Invalid environment configuration');
}

export const env = {
  nodeEnv: parsedEnv.data.NODE_ENV,
  port: parsedEnv.data.PORT,
  jwtSecret: parsedEnv.data.JWT_SECRET,
  databaseUrl: parsedEnv.data.DATABASE_URL,
  redisUrl: parsedEnv.data.REDIS_URL,
  missionQueueName: parsedEnv.data.MISSION_QUEUE_NAME,
  missionWorkerConcurrency: parsedEnv.data.MISSION_WORKER_CONCURRENCY
};
