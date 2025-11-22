import { config as loadEnv } from 'dotenv';
import { z } from 'zod';

loadEnv();

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.string().transform((value) => Number.parseInt(value, 10)).default('3000'),
  JWT_SECRET: z.string().min(1).default('change-me'),
  DATABASE_URL: z.string().optional()
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
  databaseUrl: parsedEnv.data.DATABASE_URL
};
