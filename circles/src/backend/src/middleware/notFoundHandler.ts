import { Request, Response } from 'express';

type NotFoundResponse = {
  error: string;
};

export const notFoundHandler = (req: Request, res: Response<NotFoundResponse>): void => {
  res.status(404).json({ error: `Route ${req.originalUrl} not found` });
};
