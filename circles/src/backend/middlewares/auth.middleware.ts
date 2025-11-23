import { NextFunction, Request, Response } from 'express';
import jwt from 'jsonwebtoken';

import { env } from '../config/env.js';
import { UserService } from '../services/user-service.js';
import { AppError } from '../types/app-error.type.js';

const BEARER_PREFIX = 'Bearer ';

const extractToken = (authHeader: string): string => {
  return authHeader.slice(BEARER_PREFIX.length);
};

const isValidAuthPayload = (payload: unknown): payload is Record<string, unknown> => {
  return typeof payload === 'object' && payload !== null;
};

const hasValidCredentials = (payload: Record<string, unknown>): payload is { userId: string; email: string } => {
  const { userId, email } = payload;
  return typeof userId === 'string' && typeof email === 'string';
};

const userService = new UserService();

export const requireAuth = async (req: Request, _res: Response, next: NextFunction): Promise<void> => {
  const authHeader = req.header('authorization');

  if (!authHeader?.startsWith(BEARER_PREFIX)) {
    next(new AppError('Authorization header missing or malformed', 401));
    return;
  }

  const token = extractToken(authHeader);

  try {
    const payload = jwt.verify(token, env.jwtSecret);

    if (!isValidAuthPayload(payload)) {
      next(new AppError('Invalid token payload', 401));
      return;
    }

    if (!hasValidCredentials(payload)) {
      next(new AppError('Invalid token payload', 401));
      return;
    }

    // ✅ Validate that user still exists in database
    const user = await userService.getById(payload.userId);
    if (!user) {
      next(new AppError('User not found. Token is invalid.', 401));
      return;
    }

    req.user = { userId: payload.userId, email: payload.email };
    next();
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Invalid token';
    next(new AppError(`Unauthorized: ${message}`, 401));
  }
};
