import { prisma } from '../lib/prisma.js';
import { AppError } from '../types/app-error.type.js';
import type { MatchStatus } from '../types/enums.type.js';
import type { Match } from '../types/match.type.js';

export interface MatchQueryParams {
  status?: MatchStatus;
  userId?: string;
  limit?: number;
  offset?: number;
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
    matches: Match[];
    total: number;
  }> {
    const { status, userId, limit = 20, offset = 0 } = params;

    const where: Record<string, unknown> = {};

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

    const [matches, total] = await Promise.all([
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

    return { matches, total };
  }

  /**
   * Get a single match by ID
   */
  async getMatchById(id: string): Promise<Match | null> {
    return prisma.match.findUnique({
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
  }

  /**
   * Accept a match (user agrees to connect)
   * Requires user to be one of the participants
   */
  async acceptMatch(matchId: string, userId: string): Promise<Match> {
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

    return prisma.match.update({
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
  }

  /**
   * Decline a match (user rejects the match)
   * Requires user to be one of the participants
   */
  async declineMatch(matchId: string, userId: string): Promise<Match> {
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

    return prisma.match.update({
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
  }
}

export const matchService = new MatchService();
