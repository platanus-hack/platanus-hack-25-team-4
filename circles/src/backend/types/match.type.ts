import { MatchType, MatchStatus } from './enums.type.js';

/**
 * Match model matching Prisma schema
 */
export type Match = {
  id: string;
  primaryUserId: string;
  secondaryUserId: string;
  primaryCircleId: string;
  secondaryCircleId: string;
  type: MatchType;
  worthItScore: number;
  status: MatchStatus;
  explanationSummary?: string | null;
  createdAt: Date;
  updatedAt: Date;
};

/**
 * Match creation input
 */
export type CreateMatchInput = {
  primaryUserId: string;
  secondaryUserId: string;
  primaryCircleId: string;
  secondaryCircleId: string;
  type: MatchType;
  worthItScore: number;
  status?: MatchStatus;
  explanationSummary?: string;
};

/**
 * Match update input
 */
export type UpdateMatchInput = Partial<Omit<CreateMatchInput, 'primaryUserId' | 'secondaryUserId' | 'primaryCircleId' | 'secondaryCircleId'>>;

/**
 * Match with related entities (for detailed responses)
 */
export type MatchWithDetails = Match & {
  primaryUser?: {
    id: string;
    email: string;
    firstName?: string | null;
    lastName?: string | null;
  };
  secondaryUser?: {
    id: string;
    email: string;
    firstName?: string | null;
    lastName?: string | null;
  };
  primaryCircle?: {
    id: string;
    objective: string;
  };
  secondaryCircle?: {
    id: string;
    objective: string;
  };
};

