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
    .default('5'),
  API_URL: z.string().optional().default('http://localhost:3000'),
  AWS_REGION: z.string().optional().default('us-east-1'),
  AWS_ACCESS_KEY_ID: z.string().optional(),
  AWS_SECRET_ACCESS_KEY: z.string().optional(),
  SES_FROM_EMAIL: z.string().optional().default('hola@circles.lat'),
  SES_REPLY_TO_EMAIL: z.string().optional(),
  // Observer configuration
  OBSERVER_ENABLED: z
    .string()
    .transform((value) => value !== 'false')
    .default('true'),
  OBSERVER_BATCH_SIZE: z
    .string()
    .transform((value) => Number.parseInt(value, 10))
    .default('50'),
  OBSERVER_BATCH_WAIT_MS: z
    .string()
    .transform((value) => Number.parseInt(value, 10))
    .default('100')
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
  missionWorkerConcurrency: parsedEnv.data.MISSION_WORKER_CONCURRENCY,
  apiUrl: parsedEnv.data.API_URL,
  awsRegion: parsedEnv.data.AWS_REGION,
  awsAccessKeyId: parsedEnv.data.AWS_ACCESS_KEY_ID,
  awsSecretAccessKey: parsedEnv.data.AWS_SECRET_ACCESS_KEY,
  sesFromEmail: parsedEnv.data.SES_FROM_EMAIL,
  sesReplyToEmail: parsedEnv.data.SES_REPLY_TO_EMAIL,
  // Observer configuration
  observerEnabled: parsedEnv.data.OBSERVER_ENABLED,
  observerBatchSize: parsedEnv.data.OBSERVER_BATCH_SIZE,
  observerBatchWaitMs: parsedEnv.data.OBSERVER_BATCH_WAIT_MS
};
