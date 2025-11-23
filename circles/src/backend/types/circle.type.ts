import { CircleStatus } from './enums.type.js';

/**
 * Circle model matching Prisma schema
 * Position is stored in User; Circle only has radius
 */
export type Circle = {
  id: string;
  userId: string;
  objective: string;
  radiusMeters: number | null;
  startAt: Date | null;
  expiresAt: Date | null;
  status: CircleStatus;
  createdAt: Date;
  updatedAt: Date;
};

/**
 * Circle creation input
 * Position is taken from User's current location
 * userId, startAt, and status are set by the backend
 */
export type CreateCircleInput = {
  userId: string;
  objective: string;
  radiusMeters: number;
  expiresAt?: Date | undefined;
  startAt?: Date;
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
