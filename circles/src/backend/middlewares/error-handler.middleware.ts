import { NextFunction, Request, Response } from 'express';

import { AppError } from '../types/app-error.type.js';
import { logger } from '../utils/logger.util.js';

type ErrorResponse = {
  error: string;
};

export const errorHandler = (
  error: unknown,
  _req: Request,
  res: Response<ErrorResponse>,
  _next: NextFunction
): void => {
  if (error instanceof AppError) {
    logger.warn(error.message);
    res.status(error.status).json({ error: error.message });
    return;
  }

  const unexpectedError = error instanceof Error ? error : new Error('Unknown error');
  logger.error(unexpectedError.message);
  res.status(500).json({ error: 'Internal server error' });
};
