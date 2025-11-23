import { NextFunction, Request, Response } from 'express';

import { logger } from '../utils/logger.util.js';

/**
 * Safely convert a value to string for logging
 */
const valueToString = (value: unknown): string => {
  if (typeof value === 'string') {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map(v => valueToString(v)).join(',');
  }
  if (value === null || value === undefined) {
    return '';
  }
  return String(value);
};

/**
 * Convert query parameters to URL search string
 */
const buildQueryString = (query: Record<string, unknown>): string => {
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    const stringValue = valueToString(value);
    if (stringValue) {
      params.append(key, stringValue);
    }
  });
  const result = params.toString();
  return result ? `?${result}` : '';
};

/**
 * Middleware to log incoming requests with method, path, query parameters, and body
 */
export const requestLogger = (req: Request, _res: Response, next: NextFunction): void => {
  const { method, path, query, body } = req;
  
  const queryString = buildQueryString(query);
  const fullPath = `${path}${queryString}`;
  
  const bodyInfo = body && Object.keys(body).length > 0 
    ? ` | Body: ${JSON.stringify(body)}`
    : '';
  
  logger.info(`[${method}] ${fullPath}${bodyInfo}`);
  
  next();
};

