type LogLevel = 'info' | 'warn' | 'error';

const formatMessage = (level: LogLevel, message: string): string => {
  const timestamp = new Date().toISOString();
  return `[${timestamp}] [${level.toUpperCase()}] ${message}`;
};

export const logger = {
  info: (message: string): void => {
    console.log(formatMessage('info', message));
  },
  warn: (message: string): void => {
    console.warn(formatMessage('warn', message));
  },
  error: (message: string): void => {
    console.error(formatMessage('error', message));
  }
};
