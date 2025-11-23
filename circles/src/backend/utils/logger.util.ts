import { env } from '../config/env.js';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const LOG_LEVELS = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3
};

const getCurrentLogLevel = (): number => {
  const level = env.logLevel.toLowerCase();
  if (level === 'debug' || level === 'info' || level === 'warn' || level === 'error') {
    return LOG_LEVELS[level];
  }
  return LOG_LEVELS.info;
};

const formatMessage = (level: LogLevel, message: string, data?: unknown): string => {
  const timestamp = new Date().toISOString();
  const dataStr = data ? ` ${JSON.stringify(data)}` : '';
  return `[${timestamp}] [${level.toUpperCase()}] ${message}${dataStr}`;
};

export const logger = {
  debug: (message: string, data?: unknown): void => {
    if (LOG_LEVELS.debug >= getCurrentLogLevel()) {
      console.log(formatMessage('debug', message, data));
    }
  },
  info: (message: string, data?: unknown): void => {
    if (LOG_LEVELS.info >= getCurrentLogLevel()) {
      console.log(formatMessage('info', message, data));
    }
  },
  warn: (message: string, data?: unknown): void => {
    if (LOG_LEVELS.warn >= getCurrentLogLevel()) {
      console.warn(formatMessage('warn', message, data));
    }
  },
  error: (message: string, error: unknown): void => {
    if (LOG_LEVELS.error >= getCurrentLogLevel()) {
      console.error(formatMessage('error', message), error);
    }
  }
};
