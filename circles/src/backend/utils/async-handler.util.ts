import { NextFunction, Request, RequestHandler, Response } from 'express';

type AsyncHandler = (req: Request, res: Response, next: NextFunction) => Promise<void>;

export const asyncHandler =
  (handler: AsyncHandler): RequestHandler =>
  (_req, _res, _next): void => {
    Promise.resolve(handler(_req, _res, _next)).catch(_next);
  };
