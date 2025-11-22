import { CircleStatus } from './enums.type.js';

/**
 * Circle model matching Prisma schema
 */
export type Circle = {
  id: string;
  userId: string;
  objective: string;
  centerLat: number | null;
  centerLon: number | null;
  radiusMeters: number | null;
  startAt: Date | null;
  expiresAt: Date | null;
  status: CircleStatus;
  createdAt: Date;
  updatedAt: Date;
};

/**
 * Circle creation input
 */
export type CreateCircleInput = {
  userId: string;
  objective: string;
  centerLat: number;
  centerLon: number;
  radiusMeters: number;
  startAt: Date;
  expiresAt: Date;
  status?: CircleStatus;
};

/**
 * Circle update input
 */
export type UpdateCircleInput = Partial<Omit<CreateCircleInput, 'userId'>>;

/**
 * Circle with user details (for responses)
 */
export type CircleWithUser = Circle & {
  user?: {
    id: string;
    email: string;
    firstName?: string | null;
    lastName?: string | null;
  };
};
