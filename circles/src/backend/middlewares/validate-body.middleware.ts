import { NextFunction, Request, Response } from 'express';
import { ZodSchema } from 'zod';

import { AppError } from '../types/app-error.type.js';
import { logger } from '../utils/logger.util.js';

export const validateBody =
  <T>(schema: ZodSchema<T>) =>
  (req: Request, _res: Response, next: NextFunction): void => {
    logger.warn(`Validating body: ${JSON.stringify(req.body)}`);
    const result = schema.safeParse(req.body);

    if (!result.success) {
      const message = result.error.errors.map((issue) => issue.message).join('; ');
      next(new AppError(`Validation failed: ${message}`, 400));
      return;
    }

    req.body = result.data;
    next();
  };
