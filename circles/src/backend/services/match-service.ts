import { prisma } from '../lib/prisma.js';
import { AppError } from '../types/app-error.type.js';
import { MatchStatus, MatchType } from '../types/enums.type.js';
import type { MatchWithDetails } from '../types/match.type.js';

export interface MatchQueryParams {
  status?: MatchStatus;
  userId?: string;
  limit?: number;
  offset?: number;
}

/**
 * Map Prisma MatchType to our custom MatchType
 */
function mapMatchType(prismaType: string): MatchType {
  switch (prismaType) {
    case 'match':
      return MatchType.MATCH;
    case 'soft_match':
      return MatchType.SOFT_MATCH;
    default:
      throw new Error(`Unknown MatchType: ${prismaType}`);
  }
}

/**
 * Map Prisma MatchStatus to our custom MatchStatus
 */
function mapMatchStatus(prismaStatus: string): MatchStatus {
  switch (prismaStatus) {
    case 'pending_accept':
      return MatchStatus.PENDING_ACCEPT;
    case 'active':
      return MatchStatus.ACTIVE;
    case 'declined':
      return MatchStatus.DECLINED;
    case 'expired':
      return MatchStatus.EXPIRED;
    default:
      throw new Error(`Unknown MatchStatus: ${prismaStatus}`);
  }
}

/**
 * Service for match operations
 * Handles match retrieval, acceptance, and rejection
 */
export class MatchService {
  /**
   * Get matches with optional filtering
   */
  async getMatches(params: MatchQueryParams): Promise<{
    matches: MatchWithDetails[];
    total: number;
  }> {
    const { status, userId, limit = 20, offset = 0 } = params;

    const where: {
      status?: MatchStatus;
      OR?: Array<{ primaryUserId: string } | { secondaryUserId: string }>;
    } = {};

    if (status) {
      where.status = status;
    }

    if (userId) {
      // Match where user is either primary or secondary
      where.OR = [
        { primaryUserId: userId },
        { secondaryUserId: userId }
      ];
    }

    const [prismaMatches, total] = await Promise.all([
      prisma.match.findMany({
        where,
        take: limit,
        skip: offset,
        orderBy: { createdAt: 'desc' },
        include: {
          primaryUser: {
            select: {
              id: true,
              email: true,
              firstName: true,
              lastName: true
            }
          },
          secondaryUser: {
            select: {
              id: true,
              email: true,
              firstName: true,
              lastName: true
            }
          }
        }
      }),
      prisma.match.count({ where })
    ]);

    const matches: MatchWithDetails[] = prismaMatches.map((match) => ({
      ...match,
      type: mapMatchType(match.type),
      status: mapMatchStatus(match.status)
    }));

    return { matches, total };
  }

  /**
   * Get a single match by ID
   */
  async getMatchById(id: string): Promise<MatchWithDetails | null> {
    const prismaMatch = await prisma.match.findUnique({
      where: { id },
      include: {
        primaryUser: {
          select: {
            id: true,
            email: true,
            firstName: true,
            lastName: true
          }
        },
        secondaryUser: {
          select: {
            id: true,
            email: true,
            firstName: true,
            lastName: true
          }
        }
      }
    });

    if (!prismaMatch) {
      return null;
    }

    return {
      ...prismaMatch,
      type: mapMatchType(prismaMatch.type),
      status: mapMatchStatus(prismaMatch.status)
    };
  }

  /**
   * Accept a match (user agrees to connect)
   * Requires user to be one of the participants
   */
  async acceptMatch(matchId: string, userId: string): Promise<MatchWithDetails> {
    const match = await prisma.match.findUnique({
      where: { id: matchId }
    });

    if (!match) {
      throw new AppError('Match not found', 404);
    }

    // Verify user is a participant
    const isParticipant = match.primaryUserId === userId || match.secondaryUserId === userId;
    if (!isParticipant) {
      throw new AppError('Not authorized to accept this match', 403);
    }

    // Only pending_accept matches can be accepted
    if (match.status !== 'pending_accept') {
      throw new AppError(`Cannot accept match with status: ${match.status}`, 400);
    }

    const prismaResult = await prisma.match.update({
      where: { id: matchId },
      data: {
        status: 'active'
      },
      include: {
        primaryUser: {
          select: {
            id: true,
            email: true,
            firstName: true,
            lastName: true
          }
        },
        secondaryUser: {
          select: {
            id: true,
            email: true,
            firstName: true,
            lastName: true
          }
        }
      }
    });

    return {
      ...prismaResult,
      type: mapMatchType(prismaResult.type),
      status: mapMatchStatus(prismaResult.status)
    };
  }

  /**
   * Decline a match (user rejects the match)
   * Requires user to be one of the participants
   */
  async declineMatch(matchId: string, userId: string): Promise<MatchWithDetails> {
    const match = await prisma.match.findUnique({
      where: { id: matchId }
    });

    if (!match) {
      throw new AppError('Match not found', 404);
    }

    // Verify user is a participant
    const isParticipant = match.primaryUserId === userId || match.secondaryUserId === userId;
    if (!isParticipant) {
      throw new AppError('Not authorized to decline this match', 403);
    }

    // Only pending_accept matches can be declined
    if (match.status !== 'pending_accept') {
      throw new AppError(`Cannot decline match with status: ${match.status}`, 400);
    }

    const prismaResult = await prisma.match.update({
      where: { id: matchId },
      data: {
        status: 'declined'
      },
      include: {
        primaryUser: {
          select: {
            id: true,
            email: true,
            firstName: true,
            lastName: true
          }
        },
        secondaryUser: {
          select: {
            id: true,
            email: true,
            firstName: true,
            lastName: true
          }
        }
      }
    });

    return {
      ...prismaResult,
      type: mapMatchType(prismaResult.type),
      status: mapMatchStatus(prismaResult.status)
    };
  }
}

export const matchService = new MatchService();
